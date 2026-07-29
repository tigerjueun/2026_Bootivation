#ifndef FND_H
#define FND_H
#include <stdint.h>
typedef enum{FND_CHAR_A=10,FND_CHAR_B=11,FND_CHAR_C=12,FND_CHAR_D=13,FND_CHAR_E=14,FND_CHAR_F=15,FND_CHAR_MINUS=16,FND_CHAR_BLANK=17,FND_CHAR_O=18,FND_CHAR_N=19}fnd_char_t;
void fnd_init(void);void fnd_off(void);void fnd_refresh_step(void);void fnd_set_digits(uint8_t,uint8_t,uint8_t,uint8_t);void fnd_set_zero(void);void fnd_set_item_count(fnd_char_t,uint8_t);void fnd_set_total(uint16_t);void fnd_set_done(void);
#endif
