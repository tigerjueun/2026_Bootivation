#include "app_time.h"
#include "fnd.h"
#include <util/delay.h>
void app_delay_ms(uint16_t ms){while(ms--!=0U){fnd_refresh_step();_delay_ms(1);}}
