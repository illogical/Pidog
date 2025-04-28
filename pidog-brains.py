from lib.pidog import Pidog
from lib.preset_actions import howling
import time

my_dog = Pidog()
touch_active = False  # Flag to track touch state

def main():

    while True:
        touch_status = my_dog.dual_touch.read()
        print(f"touch_status: {touch_status}")

        if touch_status != 'N' and not touch_active:
            print("Touch detected!")
            touch_active = True
            execute_command(touch_status) # Execute command based on touch status
            
        elif touch_active:
            print("Touch released.")
            touch_active = False
            

        time.sleep(0.5)

if __name__ == "__main__":
    main()


def execute_command(command):
    # Placeholder for command execution logic
    print(f"Executing command: {command}")

    my_dog.rgb_strip.set_mode('breath', color=[245, 10, 10], bps=2.5, brightness=0.8)

    my_dog.do_action('sit', speed=50)
    my_dog.head_move([[0, 0, 0]], pitch_comp=-40, immediately=True, speed=80)

    howling(my_dog)
    my_dog.wait_all_done()
    time.sleep(5)

    # Lay down again
    my_dog.rgb_strip.set_mode('breath', 'pink', bps=1)
    my_dog.do_action('lie', speed=50)
    my_dog.wait_all_done()

    # match command:
    #     case 'N':
    #         print("No touch detected.")
    #     case 'L':
    #         print("Left touch detected.")
    #         # Add logic for left touch
    #     case 'LS':
    #         print("Left slide detected.")
    #         # Add logic for left slide
    #     case 'R':
    #         print("Right touch detected.")
    #         # Add logic for right touch
    #     case 'RS':
    #         print("Right slide detected.")
    #         # Add logic for right slide
    #     case _:
    #         print("Unknown command.")

    