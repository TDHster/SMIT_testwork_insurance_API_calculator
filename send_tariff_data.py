from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime

# Инициализация базы данных
DATABASE_URL = "sqlite:///./tariffs.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модель для базы данных
class Tariff(Base):
    __tablename__ = "tariffs"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    cargo_type = Column(String, index=True)
    rate = Column(Float)

# Создаем таблицы
Base.metadata.create_all(bind=engine)

# Pydantic-модели для валидации входных данных
class TariffItem(BaseModel):
    cargo_type: str
    rate: float

class TariffData(BaseModel):
    date: str
    tariffs: list[TariffItem]

class InsuranceRequest(BaseModel):
    date: str
    cargo_type: str
    declared_value: float

# Инициализация FastAPI
app = FastAPI()

# Dependency для работы с базой данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/tariffs/")
def add_tariffs(tariff_data: dict[str, list[TariffItem]], db: Session = Depends(get_db)):
    """
    Принимает JSON с тарифами, сохраняет в базу данных.
    """
    try:
        for date_str, tariffs in tariff_data.items():
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            for item in tariffs:
                tariff = Tariff(date=date, cargo_type=item.cargo_type, rate=item.rate)
                db.add(tariff)
        db.commit()
        return {"message": "Data successfully saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tariffs/")
def get_tariffs(db: Session = Depends(get_db)):
    """
    Возвращает все тарифы из базы данных.
    """
    tariffs = db.query(Tariff).all()
    return tariffs

@app.post("/api/calculate_insurance/")
def calculate_insurance(request: InsuranceRequest, db: Session = Depends(get_db)):
    """
    Рассчитывает стоимость страхования на основе актуального тарифа.
    """
    try:
        # Преобразуем дату из строки в объект datetime
        request_date = datetime.strptime(request.date, "%Y-%m-%d").date()

        # Находим актуальный тариф для указанного типа груза и даты
        tariff = (
            db.query(Tariff)
            .filter(Tariff.cargo_type == request.cargo_type)
            .filter(Tariff.date <= request_date)
            .order_by(Tariff.date.desc())
            .first()
        )

        if not tariff:
            raise HTTPException(status_code=404, detail="Тариф не найден для указанных параметров")

        # Рассчитываем стоимость страхования
        insurance_cost = request.declared_value * tariff.rate
        return {
            "cargo_type": request.cargo_type,
            "declared_value": request.declared_value,
            "rate": tariff.rate,
            "insurance_cost": insurance_cost,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Запуск приложения
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
