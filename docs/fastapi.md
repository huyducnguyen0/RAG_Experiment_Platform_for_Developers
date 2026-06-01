Nội dung học đã học backend, fastapi:

mental model :
client gửi http request qua mạng, sau đó fast api nhận request
fast api tìm route phù hợp
fastapi gọi function python tương đương. func trả object python
fast api biến object đó thành json response và client nhận cái json nà


1. Method

    http method cho biết hành động muốn làm từ client

    GET, POST, PATCH, DELETE

2. Path

    Path là đường dẫn api, từ path có thể biết req của người dùng sẽ dùng function nào

3. Path parameter { }

    là biến trực tiếp nẳm trong path, tên nằm trong {}
    
    dùng khi cần xác định một nguồn cụ thể

4. Query parameter
    là phần sau dấu ? trong url

    dùng khi lọc, tìm kiếm , sắp xếp, phân trang, tùy chọn hiển thị
    dùng để lấy danh sách tùy chỉnh theo request

5. Body
    Request body là dữ liệu client gửi lên server, dùng với post, put, patch

    Body chứa dữ liệu lớn và phức tạp 

    Thường dùng Pydantic model để khai báo body

6. Json 
    là format của dữ liệu để trao đổi giữa client và backend
    
7. Status code là các mã số trong http response cho biết tình trạng request

8. Swagger ui
    giúp thấy rõ endpoint, input, output, trạng thái response