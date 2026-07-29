#include "fnd.h"
#include "joystick.h"
#include "lcd.h"
#include "pos.h"
#include "sensors.h"
#include "uart.h"
#include "ultrasonic.h"
#include <avr/interrupt.h>
#include <avr/io.h>
static void disable_jtag(void){MCUCSR|=_BV(JTD);MCUCSR|=_BV(JTD);}int main(void){cli();disable_jtag();uart_init();fnd_init();lcd_init();joystick_init();sensors_init();ultrasonic_init();sei();uart_puts("BOOT,ATMEGA128_POS_C");uart_newline();pos_run_forever();return 0;}
