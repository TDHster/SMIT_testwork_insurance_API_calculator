from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
from confluent_kafka import Producer, KafkaException, KafkaError
import json
import socket

# Инициализация базы данных
DATABASE_URL = "sqlite:///./tariffs.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Tariff(Base):
    __tablename__ = "tariffs"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    cargo_type = Column(String, index=True)
    rate = Column(Float)

Base.metadata.create_all(bind=engine)

class TariffItem(BaseModel):
    cargo_type: str
    rate: float

class InsuranceRequest(BaseModel):
    date: str
    cargo_type: str
    declared_value: float

# Kafka настройки
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "tariff_changes"

def is_kafka_available():
    """
    Проверяет доступность Kafka брокера.
    """
    try:
        socket.create_connection((KAFKA_BOOTSTRAP_SERVERS.split(":")[0], int(KAFKA_BOOTSTRAP_SERVERS.split(":")[1])), timeout=1)
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def create_producer():
    """
    Создает Kafka Producer. Если Kafka недоступен, возвращает None.
    """
    if not is_kafka_available():
        print("Warning: Kafka is not available.")
        return None
    try:
        producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
        return producer
    except KafkaException as e:
        print(f"Warning: Kafka is not available. Error: {e}")
        return None

producer = create_producer()

def log_change_to_kafka(user_id: int, action: str, message: str):
    """
    Логирование изменений в Kafka.
    Если Kafka недоступен, выводит предупреждение и продолжает работу.
    """
    if producer is None:
        print(f"Warning: Kafka producer is not initialized. Skipping log for action '{action}'.")
        return
    try:
        log_entry = {
            "user_id": user_id,
            "action": action,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        producer.produce(
            KAFKA_TOPIC,
            key=str(user_id),
            value=json.dumps(log_entry),
            callback=delivery_report
        )
        producer.flush()
    except KafkaException as e:
        print(f"Warning: Failed to log change to Kafka. Error: {e}")

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

# FastAPI приложение
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/update_tariff/")
def add_tariffs(
    tariff_data: dict[str, list[TariffItem]],
    db: Session = Depends(get_db),
    x_user_id: int = Header(None)
):
    try:
        added_tariffs = []
        for date_str, tariffs in tariff_data.items():
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            for item in tariffs:
                tariff = Tariff(date=date, cargo_type=item.cargo_type, rate=item.rate)
                db.add(tariff)
                db.commit()
                added_tariffs.append({"id": tariff.id, "date": date_str, "cargo_type": item.cargo_type, "rate": item.rate})

        for tariff in added_tariffs:
            log_change_to_kafka(
                user_id=x_user_id,
                action="add",
                message=f"Added tariff {tariff}"
            )

        return {"message": "Data successfully saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/delete_tariff/{tariff_id}")
def delete_tariff(
    tariff_id: int,
    db: Session = Depends(get_db),
    x_user_id: int = Header(None)
):
    try:
        tariff = db.query(Tariff).filter(Tariff.id == tariff_id).first()
        if not tariff:
            raise HTTPException(status_code=404, detail="Тариф не найден")

        db.delete(tariff)
        db.commit()

        log_change_to_kafka(
            user_id=x_user_id,
            action="delete",
            message=f"Deleted tariff with ID {tariff_id}, cargo_type {tariff.cargo_type}, rate {tariff.rate}"
        )

        return {"message": f"Тариф с ID {tariff_id} успешно удален"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Запуск сервера FastAPI
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)