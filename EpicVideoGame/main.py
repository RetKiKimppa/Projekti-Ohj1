from game_loop import start_loop

def main():
    try:
        start_loop()
    except KeyboardInterrupt:
        print("\n\n✈️  Game stopped!")
    except Exception as e:
        print(f"\n Error: {e}")


if __name__ == "__main__":
    main()