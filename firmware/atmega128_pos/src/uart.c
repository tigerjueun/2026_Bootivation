#include "uart.h"
#include "config.h"
#include <avr/io.h>
void uart_init(void){uint16_t u=(F_CPU/(16UL*UART_BAUD))-1UL;UBRR0H=u>>8;UBRR0L=u;UCSR0A=0;UCSR0B=_BV(RXEN0)|_BV(TXEN0);UCSR0C=_BV(UCSZ01)|_BV(UCSZ00);}void uart_putc(char c){while((UCSR0A&_BV(UDRE0))==0U){}UDR0=(uint8_t)c;}void uart_puts(const char*s){while(s&&*s)uart_putc(*s++);}void uart_put_u16(uint16_t v){char b[6];uint8_t i=0;if(!v){uart_putc('0');return;}while(v&&i<sizeof b){b[i++]=(char)('0'+v%10U);v/=10U;}while(i)uart_putc(b[--i]);}void uart_newline(void){uart_putc('\r');uart_putc('\n');}
