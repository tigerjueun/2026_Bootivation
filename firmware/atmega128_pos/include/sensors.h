#ifndef SENSORS_H
#define SENSORS_H
#include <stdint.h>
void sensors_init(void);uint8_t ir_product_detected(void);uint8_t touch_a_pressed(void);uint8_t touch_b_pressed(void);uint8_t touch_c_pressed(void);uint8_t touch_done_pressed(void);void wait_touch_a_release(void);void wait_touch_b_release(void);void wait_touch_c_release(void);void wait_touch_done_release(void);void led_set(uint8_t on);void led_blink_done(void);
#endif
