from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from app.schemas.experiment import (
    ExperimentComparisonResponse,
    ExperimentComparisonSummary,
    ExperimentCaseResult,
    ExperimentLeaderboardRow,
    ExperimentMetrics,
    ExperimentQuestionComparisonRow,
    ExperimentRunResponse,
    ExperimentStrategyQuestionResult,
    ExperimentSummary,
)
from app.schemas.phase_artifact import PhaseArtifact
from app.schemas.rag_config import RagConfigComponent, RagConfigPreset
from app.services.chunking_service import chunk_text_for_rag_config
from app.services.document_service import WORKSPACES_DIR
from app.services.document_service import _load_metadata, _read_document_content
from app.services.eval_question_service import list_eval_questions, repair_eval_questions_missing_chunk_ids
from app.services.evaluation_service import RetrievalEvalCase, evaluate_retrieval
from app.services.rag_config_service import (
    ANSWER_EVALUATION_RAG_STAGE,
    CONTEXT_BUILDER_RAG_STAGE,
    QUERY_TRANSFORM_RAG_STAGE,
    RERANKER_RAG_STAGE,
    get_rag_config_by_strategy,
    get_rag_config_preset,
    list_rag_config_presets,
    resolve_rag_config_identifiers,
)
from app.services.rag_phase_service import DEFAULT_RAG_PHASE_ID, validate_enabled_rag_phase
from app.services.phase_artifact_service import get_latest_phase_artifact, save_phase_artifact
from app.services.retrieval_service import SUPPORTED_RETRIEVAL_STRATEGIES

DEFAULT_COMPARISON_STAGE = DEFAULT_RAG_PHASE_ID
CHUNKING_EVALUATION_STAGE = "chunking_evaluation"
RETRIEVER_EVALUATION_STAGE = "retriever_evaluation"
QUERY_TRANSFORM_EVALUATION_STAGE = QUERY_TRANSFORM_RAG_STAGE
RERANKER_EVALUATION_STAGE = RERANKER_RAG_STAGE
CONTEXT_BUILDER_EVALUATION_STAGE = CONTEXT_BUILDER_RAG_STAGE
ANSWER_EVALUATION_STAGE = ANSWER_EVALUATION_RAG_STAGE


def run_workspace_experiment(
    workspace_id: str,
    strategy: str,
    top_k: int,
    config_id: str | None = None,
    stage: str | None = None,
) -> ExperimentRunResponse:
    if top_k <= 0:
        raise HTTPException(status_code=400, detail="top_k must be greater than 0")
    rag_config = _resolve_run_rag_config(
        workspace_id=workspace_id,
        strategy=strategy,
        config_id=config_id,
        top_k=top_k,
        stage=stage,
    )
    return _run_workspace_experiment_with_config(
        workspace_id=workspace_id,
        rag_config=rag_config,
        top_k=top_k,
    )


def _run_workspace_experiment_with_config(
    workspace_id: str,
    rag_config: RagConfigPreset,
    top_k: int,
) -> ExperimentRunResponse:
    selected_stage = rag_config.rag_stage
    selected_strategy = rag_config.strategy

    eval_questions = list_eval_questions(workspace_id)
    if not eval_questions:
        raise HTTPException(status_code=400, detail="No golden questions found in this workspace")
    if _has_missing_expected_chunk_ids(eval_questions):
        repair_eval_questions_missing_chunk_ids(workspace_id)
        eval_questions = list_eval_questions(workspace_id)

    cases = [
        RetrievalEvalCase(
            question_id=item.id,
            question=item.question,
            workspace_id=workspace_id,
            expected_chunk_ids=item.expected_chunk_ids,
            expected_evidence_texts=_resolve_expected_evidence_texts(
                workspace_id=workspace_id,
                expected_chunk_ids=item.expected_chunk_ids,
                gold_evidence_text=item.gold_evidence_text,
            ),
            top_k=top_k,
            notes=item.notes,
            reference_answer=item.reference_answer,
            keywords=item.keywords,
            category=item.category,
            label_type=item.label_type,
        )
        for item in eval_questions
    ]

    runtime_chunks = _build_runtime_chunks_for_config(
        workspace_id=workspace_id,
        rag_config=rag_config,
    )
    uses_runtime_chunks = runtime_chunks is not None
    summary, results = evaluate_retrieval(
        cases=cases,
        strategy=selected_strategy,
        chunks=runtime_chunks,
        relevance_mode="content_overlap" if selected_stage == CHUNKING_EVALUATION_STAGE or uses_runtime_chunks else "auto",
        retrieval_context_id=rag_config.config_id if uses_runtime_chunks else None,
        query_transform=_build_query_transform_function(rag_config),
        reranker=_build_reranker_function(rag_config),
        context_builder=_build_context_builder_function(rag_config),
        answer_generator=_build_answer_generator_function(rag_config),
        retrieval_top_k=_resolve_retrieval_top_k(rag_config),
    )
    created_at = datetime.now(UTC).isoformat()
    run_id = f"run_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"

    payload = {
        "run_id": run_id,
        "workspace_id": workspace_id,
        "config_id": rag_config.config_id,
        "config_name": rag_config.name,
        "rag_stage": selected_stage,
        "strategy": selected_strategy,
        "top_k": top_k,
        "created_at": created_at,
        "metrics": summary,
        "results": [_serialize_result(item) for item in results],
        "rag_config": rag_config.model_dump(),
    }

    experiment_path = _workspace_experiment_file(workspace_id, run_id)
    experiment_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report_path = _workspace_report_file(workspace_id, run_id)
    report_markdown = _build_markdown_report(payload)
    report_path.write_text(report_markdown, encoding="utf-8")

    return ExperimentRunResponse(
        run_id=run_id,
        workspace_id=workspace_id,
        config_id=rag_config.config_id,
        config_name=rag_config.name,
        rag_stage=selected_stage,
        strategy=selected_strategy,
        top_k=top_k,
        created_at=created_at,
        metrics=ExperimentMetrics(**summary),
        results=[ExperimentCaseResult(**_serialize_result(item)) for item in results],
        report_markdown_path=str(report_path),
        rag_config=rag_config,
    )


def run_workspace_experiment_comparison(
    workspace_id: str,
    strategies: list[str],
    top_k: int,
    config_ids: list[str] | None = None,
    stage: str = DEFAULT_COMPARISON_STAGE,
    candidate_pool_size: int = 5,
) -> ExperimentComparisonResponse:
    if top_k <= 0:
        raise HTTPException(status_code=400, detail="top_k must be greater than 0")
    selected_stage = stage.strip().lower() or DEFAULT_COMPARISON_STAGE
    selected_phase = validate_enabled_rag_phase(phase_id=selected_stage, workspace_id=workspace_id)
    selected_stage = selected_phase.phase_id
    if candidate_pool_size <= 0:
        raise HTTPException(status_code=400, detail="candidate_pool_size must be greater than 0")
    parent_artifact = None
    resolved_configs = _resolve_comparison_rag_configs(
        workspace_id=workspace_id,
        selected_stage=selected_stage,
        strategies=strategies,
        config_ids=config_ids,
    )
    if selected_stage == RETRIEVER_EVALUATION_STAGE:
        parent_artifact = _require_latest_chunking_artifact(workspace_id)
        resolved_configs = _build_retriever_phase_rag_configs(
            parent_artifact=parent_artifact,
            retriever_configs=resolved_configs,
        )
    elif selected_stage == QUERY_TRANSFORM_EVALUATION_STAGE:
        parent_artifact = _require_latest_retriever_artifact(workspace_id)
        resolved_configs = _build_query_transform_phase_rag_configs(
            workspace_id=workspace_id,
            parent_artifact=parent_artifact,
            query_transform_configs=resolved_configs,
        )
    elif selected_stage == RERANKER_EVALUATION_STAGE:
        parent_artifact = _require_latest_query_transform_artifact(workspace_id)
        resolved_configs = _build_reranker_phase_rag_configs(
            workspace_id=workspace_id,
            parent_artifact=parent_artifact,
            reranker_configs=resolved_configs,
        )
    elif selected_stage == CONTEXT_BUILDER_EVALUATION_STAGE:
        parent_artifact = _require_latest_reranker_artifact(workspace_id)
        resolved_configs = _build_context_builder_phase_rag_configs(
            workspace_id=workspace_id,
            parent_artifact=parent_artifact,
            context_builder_configs=resolved_configs,
        )
    elif selected_stage == ANSWER_EVALUATION_STAGE:
        parent_artifact = _require_latest_context_builder_artifact(workspace_id)
        resolved_configs = _build_answer_evaluation_phase_rag_configs(
            workspace_id=workspace_id,
            parent_artifact=parent_artifact,
            answer_configs=resolved_configs,
        )

    rag_configs = [
        _apply_rag_config_runtime_options(rag_config, top_k, selected_stage)
        for rag_config in resolved_configs
    ]

    runs = [
        _run_workspace_experiment_with_config(
            workspace_id=workspace_id,
            rag_config=rag_config,
            top_k=top_k,
        )
        for rag_config in rag_configs
    ]
    summaries = [_to_summary(run) for run in runs]
    leaderboard = _build_leaderboard(
        summaries=summaries,
        stage=selected_stage,
        candidate_pool_size=candidate_pool_size,
    )
    question_comparisons = _build_question_comparisons(runs)
    best_strategy = leaderboard[0].strategy if leaderboard else None
    ranked_summaries = _sort_summaries_by_leaderboard(summaries, leaderboard)
    summary = _build_comparison_summary(
        stage=selected_stage,
        candidate_pool_size=candidate_pool_size,
        leaderboard=leaderboard,
    )
    phase_artifact = save_phase_artifact(
        workspace_id=workspace_id,
        phase_id=selected_stage,
        candidate_pool_size=candidate_pool_size,
        leaderboard=leaderboard,
        summary=summary.model_dump(),
        parent_artifact_id=parent_artifact.artifact_id if parent_artifact else None,
        parent_phase_id=parent_artifact.phase_id if parent_artifact else None,
    )

    return ExperimentComparisonResponse(
        workspace_id=workspace_id,
        stage=selected_stage,
        top_k=top_k,
        created_at=datetime.now(UTC).isoformat(),
        best_strategy=best_strategy,
        summary=summary,
        phase_artifact=phase_artifact,
        leaderboard=leaderboard,
        rag_configs=rag_configs,
        question_comparisons=question_comparisons,
        runs=ranked_summaries,
    )


def _resolve_run_rag_config(
    workspace_id: str,
    strategy: str,
    config_id: str | None,
    top_k: int,
    stage: str | None,
) -> RagConfigPreset:
    if config_id:
        rag_config = get_rag_config_preset(config_id=config_id, workspace_id=workspace_id)
    else:
        rag_config = get_rag_config_by_strategy(strategy=strategy, workspace_id=workspace_id)

    selected_stage = stage.strip().lower() if stage else rag_config.rag_stage
    selected_phase = validate_enabled_rag_phase(phase_id=selected_stage, workspace_id=workspace_id)
    if selected_phase.phase_id == QUERY_TRANSFORM_EVALUATION_STAGE and rag_config.rag_stage == QUERY_TRANSFORM_EVALUATION_STAGE:
        return _apply_rag_config_runtime_options(
            _build_query_transform_run_config(
                workspace_id=workspace_id,
                query_transform_config=rag_config,
            ),
            top_k,
            selected_phase.phase_id,
        )
    if selected_phase.phase_id == RERANKER_EVALUATION_STAGE and rag_config.rag_stage == RERANKER_EVALUATION_STAGE:
        return _apply_rag_config_runtime_options(
            _build_reranker_run_config(
                workspace_id=workspace_id,
                reranker_config=rag_config,
            ),
            top_k,
            selected_phase.phase_id,
        )
    if selected_phase.phase_id == CONTEXT_BUILDER_EVALUATION_STAGE and rag_config.rag_stage == CONTEXT_BUILDER_EVALUATION_STAGE:
        return _apply_rag_config_runtime_options(
            _build_context_builder_run_config(
                workspace_id=workspace_id,
                context_builder_config=rag_config,
            ),
            top_k,
            selected_phase.phase_id,
        )
    if selected_phase.phase_id == ANSWER_EVALUATION_STAGE and rag_config.rag_stage == ANSWER_EVALUATION_STAGE:
        return _apply_rag_config_runtime_options(
            _build_answer_evaluation_run_config(
                workspace_id=workspace_id,
                answer_config=rag_config,
            ),
            top_k,
            selected_phase.phase_id,
        )
    if config_id and rag_config.rag_stage != selected_phase.phase_id:
        raise HTTPException(
            status_code=400,
            detail=(
                f"rag_config '{rag_config.config_id}' belongs to '{rag_config.rag_stage}', "
                f"not '{selected_phase.phase_id}'. Select a config from the active phase."
            ),
        )
    return _apply_rag_config_runtime_options(rag_config, top_k, selected_phase.phase_id)


def _resolve_comparison_rag_configs(
    workspace_id: str,
    selected_stage: str,
    strategies: list[str],
    config_ids: list[str] | None,
) -> list[RagConfigPreset]:
    if config_ids:
        resolved_configs = resolve_rag_config_identifiers(
            config_ids=config_ids,
            strategies=strategies,
            workspace_id=workspace_id,
        )
    elif selected_stage == RETRIEVER_EVALUATION_STAGE:
        resolved_configs = resolve_rag_config_identifiers(
            config_ids=None,
            strategies=strategies,
            workspace_id=workspace_id,
        )
    else:
        resolved_configs = [
            preset
            for preset in list_rag_config_presets(workspace_id=workspace_id)
            if preset.rag_stage == selected_stage
        ]

    stage_configs = [
        rag_config
        for rag_config in resolved_configs
        if rag_config.rag_stage == selected_stage
    ]
    if not stage_configs:
        raise HTTPException(
            status_code=400,
            detail=f"No rag_config presets are available for stage '{selected_stage}'",
        )

    return stage_configs


def _require_latest_chunking_artifact(workspace_id: str):
    artifact = get_latest_phase_artifact(
        workspace_id=workspace_id,
        phase_id=CHUNKING_EVALUATION_STAGE,
    )
    if artifact is None:
        raise HTTPException(
            status_code=400,
            detail="Run chunking evaluation before retriever evaluation.",
        )
    if not artifact.kept_config_ids:
        raise HTTPException(
            status_code=400,
            detail="Latest chunking evaluation artifact has no kept candidates.",
        )
    return artifact


def _require_latest_retriever_artifact(workspace_id: str):
    artifact = get_latest_phase_artifact(
        workspace_id=workspace_id,
        phase_id=RETRIEVER_EVALUATION_STAGE,
    )
    if artifact is None:
        raise HTTPException(
            status_code=400,
            detail="Run retriever evaluation before query transform evaluation.",
        )
    if not artifact.kept_config_ids:
        raise HTTPException(
            status_code=400,
            detail="Latest retriever evaluation artifact has no kept candidates.",
        )
    return artifact


def _require_latest_query_transform_artifact(workspace_id: str):
    artifact = get_latest_phase_artifact(
        workspace_id=workspace_id,
        phase_id=QUERY_TRANSFORM_EVALUATION_STAGE,
    )
    if artifact is None:
        raise HTTPException(
            status_code=400,
            detail="Run query transform evaluation before reranker evaluation.",
        )
    if not artifact.kept_config_ids:
        raise HTTPException(
            status_code=400,
            detail="Latest query transform evaluation artifact has no kept candidates.",
        )
    return artifact


def _require_latest_reranker_artifact(workspace_id: str):
    artifact = get_latest_phase_artifact(
        workspace_id=workspace_id,
        phase_id=RERANKER_EVALUATION_STAGE,
    )
    if artifact is None:
        raise HTTPException(
            status_code=400,
            detail="Run reranker evaluation before context builder evaluation.",
        )
    if not artifact.kept_config_ids:
        raise HTTPException(
            status_code=400,
            detail="Latest reranker evaluation artifact has no kept candidates.",
        )
    return artifact


def _require_latest_context_builder_artifact(workspace_id: str):
    artifact = get_latest_phase_artifact(
        workspace_id=workspace_id,
        phase_id=CONTEXT_BUILDER_EVALUATION_STAGE,
    )
    if artifact is None:
        raise HTTPException(
            status_code=400,
            detail="Run context builder evaluation before answer evaluation.",
        )
    if not artifact.kept_config_ids:
        raise HTTPException(
            status_code=400,
            detail="Latest context builder evaluation artifact has no kept candidates.",
        )
    return artifact


def _build_retriever_phase_rag_configs(
    parent_artifact: PhaseArtifact,
    retriever_configs: list[RagConfigPreset],
) -> list[RagConfigPreset]:
    kept_config_ids = set(parent_artifact.kept_config_ids)
    kept_chunking_candidates = [
        candidate
        for candidate in parent_artifact.candidates
        if candidate.status == "kept" and candidate.config_id in kept_config_ids
    ]
    if not kept_chunking_candidates:
        raise HTTPException(
            status_code=400,
            detail="Latest chunking evaluation artifact has no usable kept candidates.",
        )

    combined_configs: list[RagConfigPreset] = []
    seen_config_ids: set[str] = set()
    for chunking_candidate in kept_chunking_candidates:
        for retriever_config in retriever_configs:
            config_id = (
                f"cfg_retriever__{_combined_config_token(chunking_candidate.config_id)}"
                f"__{retriever_config.strategy}"
            )
            if config_id in seen_config_ids:
                continue

            chunking_params = {
                **chunking_candidate.chunking_params,
                "source_config_id": chunking_candidate.config_id,
                "parent_artifact_id": parent_artifact.artifact_id,
            }
            retriever_params = {
                **retriever_config.retriever.params,
                "source_chunking_config_id": chunking_candidate.config_id,
                "parent_artifact_id": parent_artifact.artifact_id,
            }
            combined_configs.append(
                RagConfigPreset(
                    config_id=config_id,
                    name=f"{chunking_candidate.config_name} + {retriever_config.name}",
                    description=(
                        "Retriever candidate generated from the latest kept chunking "
                        f"candidate '{chunking_candidate.config_id}'."
                    ),
                    rag_stage=RETRIEVER_EVALUATION_STAGE,
                    strategy=retriever_config.strategy,
                    top_k=retriever_config.top_k,
                    chunking=RagConfigComponent(
                        type=chunking_candidate.chunking_type,
                        params=chunking_params,
                    ),
                    retriever=RagConfigComponent(
                        type=retriever_config.retriever.type,
                        params=retriever_params,
                    ),
                    query_transform=retriever_config.query_transform,
                    reranker=retriever_config.reranker,
                    context_builder=retriever_config.context_builder,
                    answer_generator=retriever_config.answer_generator,
                )
            )
            seen_config_ids.add(config_id)

    return combined_configs


def _build_query_transform_run_config(
    workspace_id: str,
    query_transform_config: RagConfigPreset,
) -> RagConfigPreset:
    parent_artifact = _require_latest_retriever_artifact(workspace_id)
    kept_candidates = _get_kept_artifact_candidates(parent_artifact)
    if not kept_candidates:
        raise HTTPException(
            status_code=400,
            detail="Latest retriever evaluation artifact has no usable kept candidates.",
        )

    parent_candidate = kept_candidates[0]
    retriever_run = get_workspace_experiment(workspace_id=workspace_id, run_id=parent_candidate.run_id)
    return _combine_retriever_and_query_transform_config(
        retriever_config=retriever_run.rag_config,
        query_transform_config=query_transform_config,
        parent_artifact=parent_artifact,
    )


def _build_query_transform_phase_rag_configs(
    workspace_id: str,
    parent_artifact: PhaseArtifact,
    query_transform_configs: list[RagConfigPreset],
) -> list[RagConfigPreset]:
    kept_candidates = _get_kept_artifact_candidates(parent_artifact)
    if not kept_candidates:
        raise HTTPException(
            status_code=400,
            detail="Latest retriever evaluation artifact has no usable kept candidates.",
        )

    combined_configs: list[RagConfigPreset] = []
    seen_config_ids: set[str] = set()
    for parent_candidate in kept_candidates:
        retriever_run = get_workspace_experiment(workspace_id=workspace_id, run_id=parent_candidate.run_id)
        for query_transform_config in query_transform_configs:
            combined_config = _combine_retriever_and_query_transform_config(
                retriever_config=retriever_run.rag_config,
                query_transform_config=query_transform_config,
                parent_artifact=parent_artifact,
            )
            if combined_config.config_id in seen_config_ids:
                continue
            combined_configs.append(combined_config)
            seen_config_ids.add(combined_config.config_id)

    return combined_configs


def _build_reranker_run_config(
    workspace_id: str,
    reranker_config: RagConfigPreset,
) -> RagConfigPreset:
    parent_artifact = _require_latest_query_transform_artifact(workspace_id)
    kept_candidates = _get_kept_artifact_candidates(parent_artifact)
    if not kept_candidates:
        raise HTTPException(
            status_code=400,
            detail="Latest query transform evaluation artifact has no usable kept candidates.",
        )

    parent_candidate = kept_candidates[0]
    query_transform_run = get_workspace_experiment(workspace_id=workspace_id, run_id=parent_candidate.run_id)
    return _combine_query_transform_and_reranker_config(
        query_transform_config=query_transform_run.rag_config,
        reranker_config=reranker_config,
        parent_artifact=parent_artifact,
    )


def _build_reranker_phase_rag_configs(
    workspace_id: str,
    parent_artifact: PhaseArtifact,
    reranker_configs: list[RagConfigPreset],
) -> list[RagConfigPreset]:
    kept_candidates = _get_kept_artifact_candidates(parent_artifact)
    if not kept_candidates:
        raise HTTPException(
            status_code=400,
            detail="Latest query transform evaluation artifact has no usable kept candidates.",
        )

    combined_configs: list[RagConfigPreset] = []
    seen_config_ids: set[str] = set()
    for parent_candidate in kept_candidates:
        query_transform_run = get_workspace_experiment(workspace_id=workspace_id, run_id=parent_candidate.run_id)
        for reranker_config in reranker_configs:
            combined_config = _combine_query_transform_and_reranker_config(
                query_transform_config=query_transform_run.rag_config,
                reranker_config=reranker_config,
                parent_artifact=parent_artifact,
            )
            if combined_config.config_id in seen_config_ids:
                continue
            combined_configs.append(combined_config)
            seen_config_ids.add(combined_config.config_id)

    return combined_configs


def _build_context_builder_run_config(
    workspace_id: str,
    context_builder_config: RagConfigPreset,
) -> RagConfigPreset:
    parent_artifact = _require_latest_reranker_artifact(workspace_id)
    kept_candidates = _get_kept_artifact_candidates(parent_artifact)
    if not kept_candidates:
        raise HTTPException(
            status_code=400,
            detail="Latest reranker evaluation artifact has no usable kept candidates.",
        )

    parent_candidate = kept_candidates[0]
    reranker_run = get_workspace_experiment(workspace_id=workspace_id, run_id=parent_candidate.run_id)
    return _combine_reranker_and_context_builder_config(
        reranker_config=reranker_run.rag_config,
        context_builder_config=context_builder_config,
        parent_artifact=parent_artifact,
    )


def _build_context_builder_phase_rag_configs(
    workspace_id: str,
    parent_artifact: PhaseArtifact,
    context_builder_configs: list[RagConfigPreset],
) -> list[RagConfigPreset]:
    kept_candidates = _get_kept_artifact_candidates(parent_artifact)
    if not kept_candidates:
        raise HTTPException(
            status_code=400,
            detail="Latest reranker evaluation artifact has no usable kept candidates.",
        )

    combined_configs: list[RagConfigPreset] = []
    seen_config_ids: set[str] = set()
    for parent_candidate in kept_candidates:
        reranker_run = get_workspace_experiment(workspace_id=workspace_id, run_id=parent_candidate.run_id)
        for context_builder_config in context_builder_configs:
            combined_config = _combine_reranker_and_context_builder_config(
                reranker_config=reranker_run.rag_config,
                context_builder_config=context_builder_config,
                parent_artifact=parent_artifact,
            )
            if combined_config.config_id in seen_config_ids:
                continue
            combined_configs.append(combined_config)
            seen_config_ids.add(combined_config.config_id)

    return combined_configs


def _build_answer_evaluation_run_config(
    workspace_id: str,
    answer_config: RagConfigPreset,
) -> RagConfigPreset:
    parent_artifact = _require_latest_context_builder_artifact(workspace_id)
    kept_candidates = _get_kept_artifact_candidates(parent_artifact)
    if not kept_candidates:
        raise HTTPException(
            status_code=400,
            detail="Latest context builder evaluation artifact has no usable kept candidates.",
        )

    parent_candidate = kept_candidates[0]
    context_builder_run = get_workspace_experiment(workspace_id=workspace_id, run_id=parent_candidate.run_id)
    return _combine_context_builder_and_answer_config(
        context_builder_config=context_builder_run.rag_config,
        answer_config=answer_config,
        parent_artifact=parent_artifact,
    )


def _build_answer_evaluation_phase_rag_configs(
    workspace_id: str,
    parent_artifact: PhaseArtifact,
    answer_configs: list[RagConfigPreset],
) -> list[RagConfigPreset]:
    kept_candidates = _get_kept_artifact_candidates(parent_artifact)
    if not kept_candidates:
        raise HTTPException(
            status_code=400,
            detail="Latest context builder evaluation artifact has no usable kept candidates.",
        )

    combined_configs: list[RagConfigPreset] = []
    seen_config_ids: set[str] = set()
    for parent_candidate in kept_candidates:
        context_builder_run = get_workspace_experiment(workspace_id=workspace_id, run_id=parent_candidate.run_id)
        for answer_config in answer_configs:
            combined_config = _combine_context_builder_and_answer_config(
                context_builder_config=context_builder_run.rag_config,
                answer_config=answer_config,
                parent_artifact=parent_artifact,
            )
            if combined_config.config_id in seen_config_ids:
                continue
            combined_configs.append(combined_config)
            seen_config_ids.add(combined_config.config_id)

    return combined_configs


def _combine_retriever_and_query_transform_config(
    retriever_config: RagConfigPreset | None,
    query_transform_config: RagConfigPreset,
    parent_artifact: PhaseArtifact,
) -> RagConfigPreset:
    if retriever_config is None:
        raise HTTPException(
            status_code=400,
            detail="Retriever artifact candidate is missing rag_config details.",
        )

    transform_token = _combined_config_token(query_transform_config.query_transform.type)
    parent_token = _combined_config_token(retriever_config.config_id)
    query_transform_params = {
        **query_transform_config.query_transform.params,
        "source_retriever_config_id": retriever_config.config_id,
        "parent_artifact_id": parent_artifact.artifact_id,
    }
    return RagConfigPreset(
        config_id=f"cfg_query_transform__{parent_token}__{transform_token}",
        name=f"{retriever_config.name} + {query_transform_config.name}",
        description=(
            "Query transform candidate generated from the latest kept retriever "
            f"candidate '{retriever_config.config_id}'."
        ),
        rag_stage=QUERY_TRANSFORM_EVALUATION_STAGE,
        strategy=retriever_config.strategy,
        top_k=retriever_config.top_k,
        chunking=retriever_config.chunking,
        retriever=retriever_config.retriever,
        query_transform=RagConfigComponent(
            type=query_transform_config.query_transform.type,
            params=query_transform_params,
        ),
        reranker=retriever_config.reranker,
        context_builder=retriever_config.context_builder,
        answer_generator=retriever_config.answer_generator,
    )


def _combine_query_transform_and_reranker_config(
    query_transform_config: RagConfigPreset | None,
    reranker_config: RagConfigPreset,
    parent_artifact: PhaseArtifact,
) -> RagConfigPreset:
    if query_transform_config is None:
        raise HTTPException(
            status_code=400,
            detail="Query transform artifact candidate is missing rag_config details.",
        )

    reranker_token = _combined_config_token(reranker_config.reranker.type)
    parent_token = _combined_config_token(query_transform_config.config_id)
    reranker_params = {
        **reranker_config.reranker.params,
        "source_query_transform_config_id": query_transform_config.config_id,
        "parent_artifact_id": parent_artifact.artifact_id,
    }
    return RagConfigPreset(
        config_id=f"cfg_reranker__{parent_token}__{reranker_token}",
        name=f"{query_transform_config.name} + {reranker_config.name}",
        description=(
            "Reranker candidate generated from the latest kept query transform "
            f"candidate '{query_transform_config.config_id}'."
        ),
        rag_stage=RERANKER_EVALUATION_STAGE,
        strategy=query_transform_config.strategy,
        top_k=query_transform_config.top_k,
        chunking=query_transform_config.chunking,
        retriever=query_transform_config.retriever,
        query_transform=query_transform_config.query_transform,
        reranker=RagConfigComponent(
            type=reranker_config.reranker.type,
            params=reranker_params,
        ),
        context_builder=query_transform_config.context_builder,
        answer_generator=query_transform_config.answer_generator,
    )


def _combine_reranker_and_context_builder_config(
    reranker_config: RagConfigPreset | None,
    context_builder_config: RagConfigPreset,
    parent_artifact: PhaseArtifact,
) -> RagConfigPreset:
    if reranker_config is None:
        raise HTTPException(
            status_code=400,
            detail="Reranker artifact candidate is missing rag_config details.",
        )

    context_builder_token = _combined_config_token(context_builder_config.context_builder.type)
    parent_token = _combined_config_token(reranker_config.config_id)
    context_builder_params = {
        **context_builder_config.context_builder.params,
        "source_reranker_config_id": reranker_config.config_id,
        "parent_artifact_id": parent_artifact.artifact_id,
    }
    return RagConfigPreset(
        config_id=f"cfg_context_builder__{parent_token}__{context_builder_token}",
        name=f"{reranker_config.name} + {context_builder_config.name}",
        description=(
            "Context builder candidate generated from the latest kept reranker "
            f"candidate '{reranker_config.config_id}'."
        ),
        rag_stage=CONTEXT_BUILDER_EVALUATION_STAGE,
        strategy=reranker_config.strategy,
        top_k=reranker_config.top_k,
        chunking=reranker_config.chunking,
        retriever=reranker_config.retriever,
        query_transform=reranker_config.query_transform,
        reranker=reranker_config.reranker,
        context_builder=RagConfigComponent(
            type=context_builder_config.context_builder.type,
            params=context_builder_params,
        ),
        answer_generator=reranker_config.answer_generator,
    )


def _combine_context_builder_and_answer_config(
    context_builder_config: RagConfigPreset | None,
    answer_config: RagConfigPreset,
    parent_artifact: PhaseArtifact,
) -> RagConfigPreset:
    if context_builder_config is None:
        raise HTTPException(
            status_code=400,
            detail="Context builder artifact candidate is missing rag_config details.",
        )

    answer_token = _combined_config_token(answer_config.answer_generator.type)
    parent_token = _combined_config_token(context_builder_config.config_id)
    answer_params = {
        **answer_config.answer_generator.params,
        "source_context_builder_config_id": context_builder_config.config_id,
        "parent_artifact_id": parent_artifact.artifact_id,
    }
    return RagConfigPreset(
        config_id=f"cfg_answer__{parent_token}__{answer_token}",
        name=f"{context_builder_config.name} + {answer_config.name}",
        description=(
            "Answer evaluation candidate generated from the latest kept context builder "
            f"candidate '{context_builder_config.config_id}'."
        ),
        rag_stage=ANSWER_EVALUATION_STAGE,
        strategy=context_builder_config.strategy,
        top_k=context_builder_config.top_k,
        chunking=context_builder_config.chunking,
        retriever=context_builder_config.retriever,
        query_transform=context_builder_config.query_transform,
        reranker=context_builder_config.reranker,
        context_builder=context_builder_config.context_builder,
        answer_generator=RagConfigComponent(
            type=answer_config.answer_generator.type,
            params=answer_params,
        ),
    )


def _get_kept_artifact_candidates(parent_artifact: PhaseArtifact):
    kept_config_ids = set(parent_artifact.kept_config_ids)
    return [
        candidate
        for candidate in parent_artifact.candidates
        if candidate.status == "kept" and candidate.config_id in kept_config_ids
    ]


def _combined_config_token(config_id: str) -> str:
    return config_id.strip().lower().replace("cfg_", "")


def _apply_rag_config_runtime_options(
    rag_config: RagConfigPreset,
    top_k: int,
    stage: str,
) -> RagConfigPreset:
    retriever = rag_config.retriever.model_copy(
        update={
            "params": {
                **rag_config.retriever.params,
                "top_k": top_k,
            },
        }
    )
    return rag_config.model_copy(
        update={
            "top_k": top_k,
            "rag_stage": stage,
            "retriever": retriever,
        }
    )


def _build_query_transform_function(rag_config: RagConfigPreset):
    transform_type = rag_config.query_transform.type.strip().lower()
    if transform_type in {"", "none"}:
        return None

    if transform_type == "rewrite":
        return _rewrite_case_question

    return None


def _build_reranker_function(rag_config: RagConfigPreset):
    reranker_type = rag_config.reranker.type.strip().lower()
    if reranker_type in {"", "none"}:
        return None

    if reranker_type == "lexical_overlap":
        return _rerank_by_lexical_overlap

    return None


def _build_context_builder_function(rag_config: RagConfigPreset):
    context_builder_type = rag_config.context_builder.type.strip().lower()
    if context_builder_type in {"", "plain_top_k"}:
        return None

    if context_builder_type == "document_window":
        return _build_document_window_context

    return None


def _build_answer_generator_function(rag_config: RagConfigPreset):
    answer_generator_type = rag_config.answer_generator.type.strip().lower()
    if answer_generator_type in {"", "none"}:
        return None
    if answer_generator_type == "grounded_mock":
        return _generate_grounded_mock_answer
    if answer_generator_type == "extract_then_mock":
        return _generate_extract_then_mock_answer
    return None


def _resolve_retrieval_top_k(rag_config: RagConfigPreset) -> int | None:
    reranker_type = rag_config.reranker.type.strip().lower()
    if reranker_type in {"", "none"}:
        return None
    return max(rag_config.top_k * 3, rag_config.top_k + 5)


def _rewrite_case_question(case: RetrievalEvalCase) -> str:
    question = case.question.strip()
    if not question:
        return question

    simplified = question
    leading_patterns = [
        r"^what does (this|the) (workspace|document|corpus) say about\s+",
        r"^tell me about\s+",
        r"^explain\s+",
        r"^describe\s+",
        r"^what is\s+",
        r"^how does\s+",
        r"^how do\s+",
        r"^can you explain\s+",
    ]
    for pattern in leading_patterns:
        simplified = re.sub(pattern, "", simplified, flags=re.IGNORECASE)

    simplified = re.sub(r"[?!.:,;]+", " ", simplified)
    simplified = re.sub(r"\s+", " ", simplified).strip()
    if not simplified:
        return question
    if simplified.lower() == question.lower().strip(" ?!.,:;"):
        return question
    return simplified


def _rerank_by_lexical_overlap(question: str, results: list):
    query_tokens = _token_set(question)
    if not query_tokens:
        return results

    def rerank_score(item):
        content_tokens = _token_set(item.content)
        overlap = len(query_tokens & content_tokens)
        return (
            overlap,
            item.score,
            -item.chunk_index,
        )

    return sorted(results, key=rerank_score, reverse=True)


def _build_document_window_context(question: str, results: list):
    _ = question
    if len(results) <= 1:
        return results

    primary = results[0]
    same_document_neighbors = [
        item
        for item in results[1:]
        if item.document_id == primary.document_id and abs(item.chunk_index - primary.chunk_index) <= 1
    ]
    remaining = [
        item
        for item in results[1:]
        if item not in same_document_neighbors
    ]
    return [primary, *same_document_neighbors, *remaining]


def _generate_grounded_mock_answer(case: RetrievalEvalCase, retrieval_question: str, results: list) -> str:
    _ = case
    if not results:
        return "The available documents do not contain enough information to answer this question."

    context_lines = [
        f"[{index}] {result.document_title}: {_normalize_preview(result.content, 180)}"
        for index, result in enumerate(results[:3], start=1)
    ]
    return (
        f"Question: {retrieval_question}\n"
        "Grounded answer draft:\n"
        f"{' '.join(_normalize_preview(result.content, 120) for result in results[:2])}\n\n"
        "Evidence:\n"
        + "\n".join(context_lines)
    )


def _generate_extract_then_mock_answer(case: RetrievalEvalCase, retrieval_question: str, results: list) -> str:
    _ = case
    if not results:
        return "The available documents do not contain enough information to answer this question."

    lead = _normalize_preview(results[0].content, 220)
    return (
        f"Question: {retrieval_question}\n"
        "Answer draft from strongest source:\n"
        f"{lead}"
    )


def _normalize_preview(content: str, limit: int) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit].rstrip()}..."


def _token_set(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(token) >= 2
    }


def _load_rag_config_from_payload(payload: dict) -> RagConfigPreset:
    if payload.get("rag_config"):
        return RagConfigPreset(**_normalize_rag_config_payload(payload["rag_config"]))

    if payload.get("config_id"):
        return _apply_rag_config_runtime_options(
            get_rag_config_preset(config_id=payload["config_id"], workspace_id=payload.get("workspace_id")),
            payload.get("top_k", 5),
            payload.get("rag_stage", DEFAULT_COMPARISON_STAGE),
        )

    return _apply_rag_config_runtime_options(
        get_rag_config_by_strategy(strategy=payload.get("strategy", "keyword"), workspace_id=payload.get("workspace_id")),
        payload.get("top_k", 5),
        payload.get("rag_stage", DEFAULT_COMPARISON_STAGE),
    )


def _normalize_rag_config_payload(payload: dict) -> dict:
    return {
        **payload,
        "answer_generator": payload.get("answer_generator", {"type": "none", "params": {}}),
    }


def _build_runtime_chunks_for_config(
    workspace_id: str,
    rag_config: RagConfigPreset,
) -> list[dict] | None:
    source_config_id = str(rag_config.chunking.params.get("source_config_id", "")).strip()
    should_build_runtime_chunks = (
        rag_config.rag_stage == CHUNKING_EVALUATION_STAGE
        or bool(source_config_id)
    )
    if not should_build_runtime_chunks:
        return None

    chunking_context_id = source_config_id or rag_config.config_id
    runtime_chunks: list[dict] = []
    for document in _load_metadata(workspace_id):
        content = _read_document_content(document, workspace_id)
        chunks = chunk_text_for_rag_config(
            document_id=document["id"],
            text=content,
            rag_config=rag_config,
        )
        for chunk in chunks:
            runtime_chunk_id = f"{chunking_context_id}_{chunk.chunk_id}"
            runtime_chunks.append(
                {
                    "document_id": document["id"],
                    "document_title": document["title"],
                    "chunk_id": runtime_chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "original_text": chunk.original_text or chunk.content,
                    "headline": chunk.headline,
                    "summary": chunk.summary,
                    "start_index": chunk.start_index,
                    "end_index": chunk.end_index,
                    "document_content_length": len(content.strip()),
                    "source_path": document.get("source_path", document.get("file_name", "")),
                    "relative_path": document.get("relative_path", document.get("file_name", "")),
                    "folder_path": document.get("folder_path", ""),
                    "doc_type": document.get("doc_type", "root"),
                    "chunking_strategy": rag_config.chunking.type,
                    "chunk_size": int(rag_config.chunking.params.get("chunk_size", rag_config.chunking.params.get("max_chunk_size", 0))),
                    "chunk_overlap": int(rag_config.chunking.params.get("overlap", 0)),
                }
            )

    return runtime_chunks


def _resolve_expected_evidence_texts(
    workspace_id: str,
    expected_chunk_ids: list[str],
    gold_evidence_text: str = "",
) -> list[str]:
    if gold_evidence_text.strip():
        return [gold_evidence_text.strip()]

    expected_set = set(expected_chunk_ids)
    evidence_texts: list[str] = []

    for document in _load_metadata(workspace_id):
        for chunk in document.get("chunks", []):
            if chunk.get("chunk_id") in expected_set:
                evidence_texts.append(chunk.get("content", ""))

    return evidence_texts


def list_workspace_experiments(workspace_id: str) -> list[ExperimentSummary]:
    experiment_dir = _workspace_experiment_dir(workspace_id)
    items: list[ExperimentSummary] = []

    for file_path in sorted(experiment_dir.glob("run_*.json"), reverse=True):
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        rag_config = _load_rag_config_from_payload(payload)
        items.append(
            ExperimentSummary(
                run_id=payload["run_id"],
                workspace_id=payload["workspace_id"],
                config_id=payload.get("config_id", rag_config.config_id),
                config_name=payload.get("config_name", rag_config.name),
                rag_stage=payload.get("rag_stage", rag_config.rag_stage),
                strategy=payload["strategy"],
                top_k=payload["top_k"],
                created_at=payload["created_at"],
                metrics=ExperimentMetrics(**payload["metrics"]),
                rag_config=rag_config,
            )
        )

    return items


def _normalize_strategy_list(strategies: list[str]) -> list[str]:
    normalized: list[str] = []
    for strategy in strategies:
        selected_strategy = strategy.strip().lower()
        if not selected_strategy:
            continue
        if selected_strategy not in SUPPORTED_RETRIEVAL_STRATEGIES:
            allowed = ", ".join(sorted(SUPPORTED_RETRIEVAL_STRATEGIES))
            raise HTTPException(status_code=400, detail=f"Unsupported strategy. Allowed: {allowed}")
        if selected_strategy not in normalized:
            normalized.append(selected_strategy)

    if not normalized:
        raise HTTPException(status_code=400, detail="At least one strategy is required")

    return normalized


def _to_summary(run: ExperimentRunResponse) -> ExperimentSummary:
    return ExperimentSummary(
        run_id=run.run_id,
        workspace_id=run.workspace_id,
        config_id=run.config_id,
        config_name=run.config_name,
        rag_stage=run.rag_stage,
        strategy=run.strategy,
        top_k=run.top_k,
        created_at=run.created_at,
        metrics=run.metrics,
        rag_config=run.rag_config,
    )


def _build_leaderboard(
    summaries: list[ExperimentSummary],
    stage: str,
    candidate_pool_size: int,
) -> list[ExperimentLeaderboardRow]:
    scored_items = [
        (summary, _compute_comparison_score(summary.metrics, summaries))
        for summary in summaries
    ]
    scored_items.sort(
        key=lambda item: (
            item[1],
            item[0].metrics.hit_at_k,
            item[0].metrics.mrr,
            item[0].metrics.recall_at_k,
            -item[0].metrics.avg_latency_ms,
        ),
        reverse=True,
    )

    kept_limit = min(candidate_pool_size, len(scored_items))
    leaderboard: list[ExperimentLeaderboardRow] = []
    for rank, (summary, score) in enumerate(scored_items, start=1):
        status = "kept" if rank <= kept_limit else "pruned"
        leaderboard.append(
            ExperimentLeaderboardRow(
                rank=rank,
                run_id=summary.run_id,
                config_id=summary.config_id or f"cfg_{summary.strategy}",
                config_name=summary.config_name or _config_name(summary.strategy),
                rag_stage=summary.rag_stage or stage,
                strategy=summary.strategy,
                metrics=summary.metrics,
                score=score,
                status=status,
                verdict=_leaderboard_verdict(rank=rank, status=status, strategy=summary.strategy),
                rag_config=summary.rag_config,
            )
        )

    return leaderboard


def _compute_comparison_score(
    metrics: ExperimentMetrics,
    summaries: list[ExperimentSummary],
) -> float:
    max_latency = max((item.metrics.avg_latency_ms for item in summaries), default=0.0)
    latency_penalty = metrics.avg_latency_ms / max_latency if max_latency > 0 else 0.0
    if metrics.answer_case_count > 0:
        score = (
            0.25 * metrics.avg_answer_match_score
            + 0.25 * metrics.hit_at_k
            + 0.20 * metrics.mrr
            + 0.15 * metrics.recall_at_k
            + 0.10 * metrics.precision_at_k
            + 0.05 * metrics.answer_present_rate
            - 0.10 * latency_penalty
        )
    else:
        score = (
            0.40 * metrics.hit_at_k
            + 0.30 * metrics.mrr
            + 0.20 * metrics.recall_at_k
            + 0.10 * metrics.precision_at_k
            - 0.10 * latency_penalty
        )
    return round(max(score, 0.0), 4)


def _sort_summaries_by_leaderboard(
    summaries: list[ExperimentSummary],
    leaderboard: list[ExperimentLeaderboardRow],
) -> list[ExperimentSummary]:
    by_run_id = {summary.run_id: summary for summary in summaries}
    return [
        by_run_id[row.run_id]
        for row in leaderboard
        if row.run_id in by_run_id
    ]


def _build_question_comparisons(
    runs: list[ExperimentRunResponse],
) -> list[ExperimentQuestionComparisonRow]:
    rows_by_question_id: dict[str, dict] = {}

    for run in runs:
        for result in run.results:
            question_id = result.question_id or result.question
            row = rows_by_question_id.setdefault(
                question_id,
                {
                    "question_id": question_id,
                    "question": result.question,
                    "expected_chunk_ids": result.expected_chunk_ids,
                    "notes": result.notes,
                    "strategy_results": [],
                },
            )
            row["strategy_results"].append(
                ExperimentStrategyQuestionResult(
                    config_id=run.config_id,
                    config_name=run.config_name,
                    strategy=run.strategy,
                    run_id=run.run_id,
                    hit=result.hit,
                    returned_chunk_ids=result.returned_chunk_ids,
                    relevant_count=result.relevant_count,
                    recall_at_k=result.recall_at_k,
                    precision_at_k=result.precision_at_k,
                    reciprocal_rank=result.reciprocal_rank,
                    latency_ms=result.latency_ms,
                )
            )

    comparison_rows: list[ExperimentQuestionComparisonRow] = []
    for row in rows_by_question_id.values():
        strategy_results = sorted(
            row["strategy_results"],
            key=lambda item: _strategy_sort_order(item.strategy),
        )
        comparison_rows.append(
            ExperimentQuestionComparisonRow(
                question_id=row["question_id"],
                question=row["question"],
                expected_chunk_ids=row["expected_chunk_ids"],
                notes=row["notes"],
                winner=_question_winner(strategy_results),
                status=_question_status(strategy_results),
                strategy_results=strategy_results,
            )
        )

    comparison_rows.sort(key=lambda row: (row.status != "all_failed", row.question_id))
    return comparison_rows


def _question_winner(results: list[ExperimentStrategyQuestionResult]) -> str | None:
    hit_results = [result for result in results if result.hit]
    if not hit_results:
        return None

    winner = max(
        hit_results,
        key=lambda item: (
            item.reciprocal_rank,
            item.recall_at_k,
            item.precision_at_k,
            -item.latency_ms,
        ),
    )
    return winner.strategy


def _question_status(results: list[ExperimentStrategyQuestionResult]) -> str:
    hit_count = sum(1 for result in results if result.hit)
    if hit_count == 0:
        return "all_failed"
    if hit_count == len(results):
        return "all_hit"
    return "partial_hit"


def _strategy_sort_order(strategy: str) -> tuple[int, str]:
    order = {
        "keyword": 0,
        "vector": 1,
        "hybrid": 2,
    }
    return (order.get(strategy, 99), strategy)


def _build_comparison_summary(
    stage: str,
    candidate_pool_size: int,
    leaderboard: list[ExperimentLeaderboardRow],
) -> ExperimentComparisonSummary:
    kept_rows = [row for row in leaderboard if row.status == "kept"]
    fastest = min(
        leaderboard,
        key=lambda row: row.metrics.avg_latency_ms,
        default=None,
    )
    highest_recall = max(
        leaderboard,
        key=lambda row: row.metrics.recall_at_k,
        default=None,
    )
    best = leaderboard[0] if leaderboard else None

    return ExperimentComparisonSummary(
        stage=stage,
        total_configs=len(leaderboard),
        candidate_pool_size=candidate_pool_size,
        kept_count=len(kept_rows),
        best_config_id=best.config_id if best else None,
        best_config_name=best.config_name if best else None,
        fastest_config_name=fastest.config_name if fastest else None,
        highest_recall_config_name=highest_recall.config_name if highest_recall else None,
        recommendation=_comparison_recommendation(best=best, kept_count=len(kept_rows)),
    )


def _comparison_recommendation(
    best: ExperimentLeaderboardRow | None,
    kept_count: int,
) -> str:
    if best is None:
        return "No candidate was evaluated. Upload golden questions and rerun the experiment."

    return (
        f"Keep {kept_count} candidate(s) for the next RAG phase. "
        f"Current best candidate is {best.config_name} based on retrieval score."
    )


def _leaderboard_verdict(rank: int, status: str, strategy: str) -> str:
    if rank == 1:
        return "Best candidate for this RAG phase"
    if status == "kept":
        return "Keep for controlled combination"
    return f"Prune {strategy} in this phase unless it becomes useful in a later combination"


def _config_name(strategy: str) -> str:
    try:
        return get_rag_config_by_strategy(strategy=strategy).name
    except HTTPException:
        return strategy.replace("_", " ").title()


def get_workspace_experiment(workspace_id: str, run_id: str) -> ExperimentRunResponse:
    payload = _load_experiment_payload(workspace_id, run_id)
    rag_config = _load_rag_config_from_payload(payload)
    return ExperimentRunResponse(
        run_id=payload["run_id"],
        workspace_id=payload["workspace_id"],
        config_id=payload.get("config_id", rag_config.config_id),
        config_name=payload.get("config_name", rag_config.name),
        rag_stage=payload.get("rag_stage", rag_config.rag_stage),
        strategy=payload["strategy"],
        top_k=payload["top_k"],
        created_at=payload["created_at"],
        metrics=ExperimentMetrics(**payload["metrics"]),
        results=[ExperimentCaseResult(**_normalize_result_payload(item)) for item in payload["results"]],
        report_markdown_path=str(_workspace_report_file(workspace_id, run_id)),
        rag_config=rag_config,
    )


def get_workspace_report_markdown(workspace_id: str, run_id: str) -> str:
    report_file = _workspace_report_file(workspace_id, run_id)
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return report_file.read_text(encoding="utf-8")


def _load_experiment_payload(workspace_id: str, run_id: str) -> dict:
    experiment_file = _workspace_experiment_file(workspace_id, run_id)
    if not experiment_file.exists():
        raise HTTPException(status_code=404, detail="Experiment run not found")
    return json.loads(experiment_file.read_text(encoding="utf-8"))


def _workspace_experiment_dir(workspace_id: str) -> Path:
    directory = WORKSPACES_DIR / workspace_id / "experiments"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _workspace_experiment_file(workspace_id: str, run_id: str) -> Path:
    return _workspace_experiment_dir(workspace_id) / f"{run_id}.json"


def _workspace_report_file(workspace_id: str, run_id: str) -> Path:
    report_dir = WORKSPACES_DIR / workspace_id / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir / f"{run_id}.md"


def _serialize_result(item: object) -> dict:
    return {
        "question_id": item.question_id,
        "question": item.question,
        "workspace_id": item.workspace_id,
        "top_k": item.top_k,
        "notes": item.notes,
        "expected_chunk_ids": item.expected_chunk_ids,
        "returned_chunk_ids": item.returned_chunk_ids,
        "returned_source_paths": item.returned_source_paths,
        "returned_doc_types": item.returned_doc_types,
        "label_type": item.label_type,
        "relevant_count": item.relevant_count,
        "hit": item.hit,
        "recall_at_k": item.recall_at_k,
        "precision_at_k": item.precision_at_k,
        "reciprocal_rank": item.reciprocal_rank,
        "latency_ms": item.latency_ms,
        "generated_answer": item.generated_answer,
        "reference_answer": item.reference_answer,
        "source_count": item.source_count,
        "answer_present": item.answer_present,
        "answer_match_score": item.answer_match_score,
    }


def _normalize_result_payload(item: dict) -> dict:
    if item.get("question_id"):
        return {
            **item,
            "label_type": item.get("label_type", "strong_chunk_ids"),
            "generated_answer": item.get("generated_answer", ""),
            "reference_answer": item.get("reference_answer", ""),
            "source_count": item.get("source_count", 0),
            "answer_present": item.get("answer_present", False),
            "answer_match_score": item.get("answer_match_score", 0.0),
        }
    return {
        **item,
        "question_id": item.get("question", ""),
        "notes": item.get("notes", ""),
        "returned_source_paths": item.get("returned_source_paths", []),
        "returned_doc_types": item.get("returned_doc_types", []),
        "label_type": item.get("label_type", "strong_chunk_ids"),
        "generated_answer": item.get("generated_answer", ""),
        "reference_answer": item.get("reference_answer", ""),
        "source_count": item.get("source_count", 0),
        "answer_present": item.get("answer_present", False),
        "answer_match_score": item.get("answer_match_score", 0.0),
    }


def _build_markdown_report(payload: dict) -> str:
    metrics = payload["metrics"]
    failed_results = [result for result in payload["results"] if not result["hit"]]
    zero_return_results = [result for result in payload["results"] if not result["returned_chunk_ids"]]
    lines = [
        "# Workspace Retrieval Experiment Report",
        "",
        f"- Run ID: {payload['run_id']}",
        f"- Workspace: {payload['workspace_id']}",
        f"- Config ID: {payload.get('config_id', '(legacy)')}",
        f"- Config Name: {payload.get('config_name', _config_name(payload['strategy']))}",
        f"- RAG Stage: {payload.get('rag_stage', DEFAULT_COMPARISON_STAGE)}",
        f"- Strategy: {payload['strategy']}",
        f"- Top K: {payload['top_k']}",
        f"- Created At (UTC): {payload['created_at']}",
        "",
        "## Metrics",
        "",
        f"- Cases: {metrics['case_count']}",
        f"- Hits: {metrics['hit_count']}",
        f"- Failed Cases: {len(failed_results)}",
        f"- Empty Retrieval Cases: {len(zero_return_results)}",
        f"- Hit@k: {metrics['hit_at_k']:.4f}",
        f"- Recall@k: {metrics['recall_at_k']:.4f}",
        f"- Precision@k: {metrics['precision_at_k']:.4f}",
        f"- MRR: {metrics['mrr']:.4f}",
        f"- Avg Latency (ms): {metrics['avg_latency_ms']:.2f}",
        f"- Chunk Count: {metrics.get('chunk_count', 0)}",
        f"- Avg Chunk Size: {metrics.get('avg_chunk_size', 0.0):.2f}",
        f"- Min Chunk Size: {metrics.get('min_chunk_size', 0)}",
        f"- Max Chunk Size: {metrics.get('max_chunk_size', 0)}",
        f"- Coverage Ratio: {metrics.get('coverage_ratio', 0.0):.4f}",
        f"- Answer Cases: {metrics.get('answer_case_count', 0)}",
        f"- Answer Reference Cases: {metrics.get('answer_reference_case_count', 0)}",
        f"- Answer Present Rate: {metrics.get('answer_present_rate', 0.0):.4f}",
        f"- Avg Answer Match Score: {metrics.get('avg_answer_match_score', 0.0):.4f}",
        "",
    ]

    if failed_results:
        lines.extend(
            [
                "## Failed Cases Overview",
                "",
            ]
        )

        for index, result in enumerate(failed_results, start=1):
            lines.extend(
                [
                    f"### Failed Case {index}",
                    f"- Question ID: {result.get('question_id', '(unknown)')}",
                    f"- Question: {result['question']}",
                    f"- Expected Count: {len(result['expected_chunk_ids'])}",
                    f"- Returned Count: {len(result['returned_chunk_ids'])}",
                    f"- Expected: {', '.join(result['expected_chunk_ids']) if result['expected_chunk_ids'] else '(none)'}",
                    f"- Returned: {', '.join(result['returned_chunk_ids']) if result['returned_chunk_ids'] else '(none)'}",
                    f"- Returned Sources: {', '.join(result.get('returned_source_paths', [])) or '(none)'}",
                    f"- Returned Doc Types: {', '.join(result.get('returned_doc_types', [])) or '(none)'}",
                    f"- Notes: {result['notes'] or '(none)'}",
                    f"- Generated Answer: {result.get('generated_answer', '') or '(none)'}",
                    f"- Reference Answer: {result.get('reference_answer', '') or '(none)'}",
                    f"- Answer Match Score: {result.get('answer_match_score', 0.0):.4f}",
                    "",
                ]
            )

    lines.extend(
        [
        "## Per-Question Results",
        "",
        ]
    )

    for index, result in enumerate(payload["results"], start=1):
        lines.extend(
            [
                f"### Case {index}",
                f"- Question ID: {result.get('question_id', '(unknown)')}",
                f"- Question: {result['question']}",
                f"- Status: {'PASS' if result['hit'] else 'FAIL'}",
                f"- Notes: {result['notes'] or '(none)'}",
                f"- Expected Count: {len(result['expected_chunk_ids'])}",
                f"- Returned Count: {len(result['returned_chunk_ids'])}",
                f"- Returned: {', '.join(result['returned_chunk_ids']) if result['returned_chunk_ids'] else '(none)'}",
                f"- Expected: {', '.join(result['expected_chunk_ids']) if result['expected_chunk_ids'] else '(none)'}",
                f"- Returned Sources: {', '.join(result.get('returned_source_paths', [])) or '(none)'}",
                f"- Returned Doc Types: {', '.join(result.get('returned_doc_types', [])) or '(none)'}",
                f"- Hit: {result['hit']}",
                f"- Recall@k: {result['recall_at_k']:.4f}",
                f"- Precision@k: {result['precision_at_k']:.4f}",
                f"- RR: {result['reciprocal_rank']:.4f}",
                f"- Latency (ms): {result['latency_ms']:.2f}",
                f"- Source Count: {result.get('source_count', 0)}",
                f"- Generated Answer: {result.get('generated_answer', '') or '(none)'}",
                f"- Reference Answer: {result.get('reference_answer', '') or '(none)'}",
                f"- Answer Present: {result.get('answer_present', False)}",
                f"- Answer Match Score: {result.get('answer_match_score', 0.0):.4f}",
                "",
            ]
        )

    return "\n".join(lines)


def _has_missing_expected_chunk_ids(eval_questions: list[object]) -> bool:
    return any(
        not item.expected_chunk_ids
        or not any(str(chunk_id).strip() for chunk_id in item.expected_chunk_ids)
        for item in eval_questions
    )
