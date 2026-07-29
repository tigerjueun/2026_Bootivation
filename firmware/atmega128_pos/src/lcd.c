#include "lcd.h"
#include <avr/io.h>
#include <util/delay.h>
#define RS PF2
#define EN PF3
static void pulse(void){PORTF|=_BV(EN);_delay_us(1);PORTF&=~_BV(EN);_delay_us(50);}static void nibble(uint8_t n){PORTF=(PORTF&0x0FU)|((n&0x0FU)<<4);pulse();}static void send(uint8_t v,uint8_t rs){if(rs)PORTF|=_BV(RS);else PORTF&=~_BV(RS);nibble(v>>4);nibble(v);}static void command(uint8_t c){send(c,0);if(c==1||c==2)_delay_ms(2);}void lcd_init(void){DDRF|=0xFCU;PORTF&=0x03U;_delay_ms(40);nibble(3);_delay_ms(5);nibble(3);_delay_ms(1);nibble(3);nibble(2);command(0x28);command(0x0C);command(0x06);lcd_clear();}void lcd_clear(void){command(1);}void lcd_goto(uint8_t row,uint8_t col){if(col>15)col=15;command((row?0xC0:0x80)+col);}void lcd_putc(char c){send((uint8_t)c,1);}void lcd_puts(const char*s){uint8_t n=0;while(s&&*s&&n++<16)lcd_putc(*s++);}static void padded(const char*s){uint8_t n=0;while(s&&*s&&n<16){lcd_putc(*s++);n++;}while(n++<16)lcd_putc(' ');}void lcd_show_lines(const char*a,const char*b){lcd_goto(0,0);padded(a);lcd_goto(1,0);padded(b);}
