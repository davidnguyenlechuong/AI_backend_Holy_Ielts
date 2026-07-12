from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """
    Base schema cho tất cả các Request và Response.
    Các schema khác trong dự án đều nên kế thừa từ class này.
    """
    model_config = ConfigDict(
        from_attributes=True,   # Cho phép convert tự động từ SQLAlchemy model sang Pydantic (orm_mode cũ)
        populate_by_name=True,  # Cho phép khởi tạo bằng cả field name và alias
        str_strip_whitespace=True # Tự động loại bỏ khoảng trắng thừa ở đầu và cuối chuỗi
    )
