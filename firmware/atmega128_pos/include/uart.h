#ifndef UART_H
#define UART_H
#include <stdint.h>
void uart_init(void);void uart_putc(char c);void uart_puts(const char*s);void uart_put_u16(uint16_t value);void uart_newline(void);
#endif
