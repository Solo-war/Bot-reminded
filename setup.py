from setuptools import setup, find_packages

setup(
    name="reminderbot",
    version="0.1.0",
    description="Mercurple reminder bot built with aiogram",
    author="Mercurple Team",
    python_requires=">=3.10",
    packages=find_packages(),  # автоматически найдёт reminderbot/ и все модули
    install_requires=[
        "aiogram>=3.4",
        "APScheduler>=3.10",
        "SQLAlchemy>=2.0",
        "alembic>=1.13",
        "pydantic>=2.4",
        "pydantic-settings>=2.2",
        "python-dotenv>=1.0",
        "fastapi>=0.110",
        "uvicorn[standard]>=0.29",
        "babel>=2.12",
        "python-i18n>=0.3",
        "tzdata>=2024.1",
        "httpx>=0.27",
        "PyYAML>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0",
            "pytest-asyncio>=0.23",
            "pytest-mock>=3.12",
            "coverage>=7.4",
        ]
    }
)
