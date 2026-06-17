from src.domain.driver_reasoning import format_driver_summary

def main():
    summary ={
        "gold": ["supportive", "negative"],
        "silver": ["supportive", "negative"],
        "details": [
            "inflation (1) -> gold: supportive, silver: supportive",
            "rates (2) -> gold: negative, silver: negative"
        ]

        #   "gold": [],
        # "silver": [],
        # "details": []
    }

    result = format_driver_summary(summary)
    print(type(result))
    print(result)

if __name__ == "__main__":
    main()