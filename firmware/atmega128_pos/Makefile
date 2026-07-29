MCU:=atmega128
F_CPU:=16000000UL
TARGET:=MicroProject_C
CC:=avr-gcc
OBJCOPY:=avr-objcopy
SIZE:=avr-size
SRC:=$(wildcard src/*.c)
OBJ:=$(SRC:.c=.o)
INCLUDES:=-Iinclude
CFLAGS:=-mmcu=$(MCU) -DF_CPU=$(F_CPU) -Os -std=gnu11 -Wall -Wextra -ffunction-sections -fdata-sections $(INCLUDES)
LDFLAGS:=-mmcu=$(MCU) -Wl,--gc-sections
.PHONY: all clean size
all: firmware/$(TARGET).hex size
firmware/$(TARGET).elf: $(OBJ) | firmware
	$(CC) $(LDFLAGS) -o $@ $(OBJ)
firmware/$(TARGET).hex: firmware/$(TARGET).elf
	$(OBJCOPY) -O ihex -R .eeprom $< $@
src/%.o: src/%.c
	$(CC) $(CFLAGS) -c $< -o $@
firmware:
	mkdir -p firmware
size: firmware/$(TARGET).elf
	$(SIZE) -C --mcu=$(MCU) $<
clean:
	rm -f src/*.o firmware/$(TARGET).elf firmware/$(TARGET).hex
