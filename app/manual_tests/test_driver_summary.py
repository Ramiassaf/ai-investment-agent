from src.domain.driver_reasoning import summarize_driver_impact

def main():
    driver_counts = {
        "inflation": 1,
        "rates": 2
    }
    # print("Counts", driver_counts)
    result = summarize_driver_impact(driver_counts)
    print(result)

if __name__ == "__main__":
    main()

