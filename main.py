import numpy as np
import pandas as pd


def main():
    print("Hello from hackathon-01!")
    print()

    # Test numpy
    print("=== NumPy Test ===")
    arr = np.array([1, 2, 3, 4, 5])
    print(f"NumPy array: {arr}")
    print(f"Mean: {arr.mean()}, Sum: {arr.sum()}, Std: {arr.std():.2f}")
    print(f"NumPy version: {np.__version__}")
    print()

    # Test pandas
    print("=== Pandas Test ===")
    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [25, 30, 35],
        "score": [85.5, 92.0, 78.5]
    })
    print(df)
    print(f"\nDataFrame shape: {df.shape}")
    print(f"Pandas version: {pd.__version__}")
    print()

    print("All imports working correctly!")


if __name__ == "__main__":
    main()
