from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import BaseModel

server = "DESKTOP-1JQGNJN"
database = "Airbase"

connectionString = f"mssql+pyodbc://@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"

engine = create_engine(connectionString)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class City(Base):
    __tablename__ = 'Cities'

    ID_city = Column(Integer, primary_key=True, index=True)
    city_name = Column(String, unique=True, nullable=False)
    airport_name = Column(String, unique=True, nullable=False)

Base.metadata.create_all(engine)


class CityCreate(BaseModel):
    city_name: str
    airport_name: str

class CityResponse(BaseModel):
    ID_city: int
    city_name: str
    airport_name: str

    model_config = {"from_attributes": True}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()

@app.post("/cities", response_model=CityResponse, status_code=201, tags=["Cities"], summary="Создать город")
def create_city(city: CityCreate, db: Session = Depends(get_db)):
    try:
        db_city = City(city_name=city.city_name, airport_name=city.airport_name)
        db.add(db_city)
        db.commit()
        db.refresh(db_city)
        return db_city
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Город или аэропорт уже существует: {e}")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка создания города: {e}")

@app.get("/cities", response_model=list[CityResponse], tags=["Cities"], summary="Все города")
def get_cities(db: Session = Depends(get_db)):
    cities = db.query(City).all()
    return cities

@app.get("/cities/{cityID}", response_model=CityResponse, tags=["Cities"], summary="Найти город")
def get_city(cityID: int, db: Session = Depends(get_db)):
    city = db.query(City).filter(City.ID_city == cityID).first()
    if not city:
        raise HTTPException(status_code=404, detail="Город не найден")
    return city

@app.put("/cities/{cityID}", response_model=CityResponse, tags=["Cities"], summary="Обновить город")
def update_city(cityID: int, city: CityCreate, db: Session = Depends(get_db)):
    db_city = db.query(City).filter(City.ID_city == cityID).first()
    if not db_city:
        raise HTTPException(status_code=404, detail="Город не найден")
    db_city.city_name = city.city_name
    db_city.airport_name = city.airport_name
    db.commit()
    return db_city

@app.delete("/cities/{cityID}", tags=["Cities"], summary="Удалить город")
def delete_city(cityID: int, db: Session = Depends(get_db)):
    db_city = db.query(City).filter(City.ID_city == cityID).first()
    if not db_city:
        raise HTTPException(status_code=404, detail="Город не найден")
    db.delete(db_city)
    db.commit()
    return {"message": "Город успешно удален"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)