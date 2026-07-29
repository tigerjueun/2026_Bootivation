#ifndef LCD_H
#define LCD_H
#include <stdint.h>
void lcd_init(void);void lcd_clear(void);void lcd_goto(uint8_t row,uint8_t column);void lcd_putc(char c);void lcd_puts(const char*s);void lcd_show_lines(const char*l1,const char*l2);
#endif
