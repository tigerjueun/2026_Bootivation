#ifndef POS_H
#define POS_H
#include <stdint.h>
typedef enum{USER_NONE=0,USER_CUSTOMER=1,USER_RIDER=2}user_mode_t;
typedef enum{POS_WAIT_SCAN=0,POS_SELECT=1,POS_WAIT_REMOVE=2,POS_DONE=3}pos_state_t;
typedef struct{user_mode_t user_mode;uint8_t count_a,count_b,count_c;uint16_t total_count;uint8_t payment_done;uint16_t session_id;}pos_data_t;
extern volatile pos_data_t g_pos_data;void pos_run_forever(void);void pos_get_snapshot(pos_data_t*out);void pos_data_changed(const pos_data_t*data);
#endif
