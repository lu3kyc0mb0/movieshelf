import menu

def main():
    while True:
        menu.menu_print()
        try:
            choice = input("Enter your number: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not menu.select(choice):
            break

if __name__ == "__main__":
    main()