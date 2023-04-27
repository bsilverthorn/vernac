import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("N", type=int, help="Enter an integer N")
    args = parser.parse_args()

    for i in range(1, args.N + 1):
        if i % 3 == 0 and i % 5 == 0:
            print("fizzbuzz")
        elif i % 3 == 0:
            print("fizz")
        elif i % 5 == 0:
            print("bizz")
        else:
            print(i)

if __name__ == "__main__":
    main()
