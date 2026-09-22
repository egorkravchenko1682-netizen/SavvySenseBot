from core import SavvyCore
from core.models import SavvyRequest


def main():
    core = SavvyCore()

    tests = [
        SavvyRequest(text="Нужен айфон до 800$"),
        SavvyRequest(text="Найди дешевле"),
        SavvyRequest(text="Сравни iPhone и Samsung"),
        SavvyRequest(text="Стоит ли покупать этот товар?"),
        SavvyRequest(text="Следи за ценой"),
        SavvyRequest(url="https://example.com/product"),
    ]

    for test in tests:
        result = core.process(test)

        print(
            f"INPUT: {test.text or test.url}"
        )
        print(
            f"SUCCESS: {result.success}"
        )
        print(
            f"INTENT: {result.intent}"
        )
        print(
            f"REGION: {result.data.get('region')}"
        )
        print(
            f"CURRENCY: {result.data.get('currency')}"
        )
        print("-" * 40)


if __name__ == "__main__":
    main()