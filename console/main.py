import menu

def main():
    if menu.MENU_DATA is None:
        return
    while True:
        menu.menu_print()
        try:
            choice = input("Enter your number: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        try:
            if not menu.select(choice):
                break
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()
