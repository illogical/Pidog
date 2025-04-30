from lib.pidog.pidog import Pidog
import time

def main():
    my_dog = Pidog()

    try:
        touch_active = False  # Flag to track touch state
        print("Touch sensor waiting...")

        while True:
            touch_status = my_dog.dual_touch.read()

            if touch_status != 'N' and not touch_active:
                print("Touch detected!")
                touch_active = True
                wake_up(my_dog)

                #execute_command(my_dog, touch_status) # Execute command based on touch status
            elif touch_active:
                print("Touch released.")
                touch_active = False
                
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\033[31mERROR: {e}\033[m")
    finally:
        print("\ngoing to sleep ...")
        my_dog.close()

def execute_command(my_dog, command):
    # Placeholder for command execution logic
    print(f"Executing command: {command}")

    my_dog.rgb_strip.set_mode('breath', color=[245, 10, 10], bps=2.5, brightness=0.8)

    howling(my_dog)
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

def sample_howl(my_dog):
    my_dog.speak('howling', 100)
    my_dog.do_action('sit', speed=80)
    my_dog.head_move([[0, 0, -30]], speed=70)
    my_dog.wait_all_done()
    time.sleep(3)
    my_dog.do_action('lie', speed=50)
    my_dog.wait_all_done()
    my_dog.speak('snoring', 100)
    my_dog.wait_all_done()
    time.sleep(2)

def howling(my_dog, volume=100):
    my_dog.do_action('sit', speed=80)
    my_dog.head_move([[0, 0, -30]], speed=95)
    my_dog.wait_all_done()

    my_dog.rgb_strip.set_mode('speak', color='cyan', bps=0.6)
    my_dog.do_action('half_sit', speed=80)
    my_dog.head_move([[0, 0, -60]], speed=80)
    my_dog.wait_all_done()
    my_dog.speak('howling', volume)
    my_dog.do_action('sit', speed=60)
    my_dog.head_move([[0, 0, 10]], speed=70)
    my_dog.wait_all_done()

    my_dog.do_action('sit', speed=60)
    my_dog.head_move([[0, 0, 10]], speed=80)
    my_dog.wait_all_done()

    time.sleep(2.34)
    my_dog.do_action('sit', speed=80)
    my_dog.head_move([[0, 0, -40]], speed=80)
    my_dog.wait_all_done()

def wake_up(my_dog):
    # stretch
    my_dog.rgb_strip.set_mode('listen', color='yellow', bps=0.6, brightness=0.8)
    my_dog.do_action('stretch', speed=50)
    my_dog.head_move([[0, 0, 30]]*2, immediately=True)
    my_dog.wait_all_done()
    time.sleep(0.3)
    my_dog.head_move([[0, 0, 0]], immediately=True, speed=70)
    my_dog.do_action('stand', speed=50)
    my_dog.wait_all_done()
    time.sleep(2)
    # sit and wag_tail
    my_dog.head_move([[0, 0, -30]], immediately=True, speed=70)
    my_dog.do_action('sit', speed=25)
    my_dog.wait_legs_done()
    #my_dog.head_move([[-20, 15, -20]], speed=60)
    time.sleep(1)
    my_dog.rgb_strip.set_mode('speak', color='cyan', bps=0.6)
    my_dog.do_action('half_sit', speed=80)
    my_dog.speak('howling', 100)
    my_dog.head_move([[0, 0, 20]], speed=80)
    my_dog.do_action('wag_tail', step_count=10, speed=100)
    my_dog.rgb_strip.set_mode('breath', color=[245, 10, 10], bps=2.5, brightness=0.8)
    my_dog.wait_all_done()
    time.sleep(0.5)
    my_dog.head_move([[0, 0, -20]], speed=50)
    # hold
    my_dog.do_action('wag_tail', step_count=10, speed=80)
    my_dog.rgb_strip.set_mode('breath', 'pink', bps=0.5)
    my_dog.wait_all_done()
    time.sleep(0.5)
    my_dog.stop_and_lie()
    my_dog.rgb_strip.close()


if __name__ == "__main__":
    main()