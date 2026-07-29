#include "ultrasonic.h"
#include "config.h"
#include <avr/io.h>
#include <util/delay.h>
void ultrasonic_init(void){DDRD|=_BV(PD2);DDRD&=~_BV(PD3);PORTD&=~(_BV(PD2)|_BV(PD3));TCCR1A=0;TCCR1B=_BV(CS11);TCNT1=0;}uint8_t ultrasonic_is_near(void){PORTD&=~_BV(PD2);_delay_us(2);PORTD|=_BV(PD2);_delay_us(10);PORTD&=~_BV(PD2);TCNT1=0;while((PIND&_BV(PD3))==0U)if(TCNT1>=ULTRA_TIMEOUT_TICKS)return 0;TCNT1=0;while(PIND&_BV(PD3))if(TCNT1>=ULTRA_TIMEOUT_TICKS)return 0;return TCNT1<ULTRA_NEAR_TICKS;}
