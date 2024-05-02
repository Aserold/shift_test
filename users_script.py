from decimal import Decimal
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import User


def load_users(file: str) -> None:
    engine = create_engine("sqlite:///db.sqlite3", echo=True)

    with open(file, 'r', encoding='UTF-8') as f:
        lines = f.read().splitlines()

    for line in lines[1:]:
        line_data = line.split(',')
        name = line_data[0]
        password = line_data[1]
        salary = Decimal(line_data[2])
        formated_date = list(map(int, line_data[3].split('.')))
        date = datetime(
            day=formated_date[0],
            month=formated_date[1],
            year=formated_date[2])
        with Session(engine) as session:
            user = User(
                username=name,
                password=password,
                salary=salary,
                promotion_date=date)
            session.add(user)
            session.commit()
    return 'Users loaded'
