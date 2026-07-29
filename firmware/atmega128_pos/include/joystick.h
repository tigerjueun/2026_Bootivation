#ifndef JOYSTICK_H
#define JOYSTICK_H
#include <stdint.h>
typedef enum{JOY_CENTER=0,JOY_LEFT=1,JOY_RIGHT=2,JOY_PRESSED=3}joystick_event_t;
void joystick_init(void);uint16_t joystick_read_adc(void);joystick_event_t joystick_get_direction(void);joystick_event_t joystick_get_stable_event(void);uint8_t joystick_is_pressed(void);void joystick_wait_center(void);void joystick_wait_button_release(void);
#endif
