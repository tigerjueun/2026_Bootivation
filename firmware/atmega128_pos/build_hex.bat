@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "TOOLCHAIN="
for %%P in ("%ProgramFiles(x86)%\Microchip\Studio\7.0\toolchain\avr8\avr8-gnu-toolchain\bin" "%ProgramFiles(x86)%\Atmel\Studio\7.0\toolchain\avr8\avr8-gnu-toolchain\bin") do if exist "%%~P\avr-gcc.exe" set "TOOLCHAIN=%%~P"
if defined TOOLCHAIN set "PATH=%TOOLCHAIN%;%PATH%"
where avr-gcc.exe >nul 2>nul || (echo [ERROR] avr-gcc.exe not found.& exit /b 1)
if not exist firmware mkdir firmware
if not exist build mkdir build
set "CFLAGS=-mmcu=atmega128 -DF_CPU=16000000UL -Os -std=gnu11 -Wall -Wextra -ffunction-sections -fdata-sections -Iinclude"
for %%F in (src\*.c) do avr-gcc %CFLAGS% -c "%%F" -o "build\%%~nF.o" || exit /b 1
avr-gcc -mmcu=atmega128 -Wl,--gc-sections build\*.o -o firmware\MicroProject_C.elf || exit /b 1
avr-objcopy -O ihex -R .eeprom firmware\MicroProject_C.elf firmware\MicroProject_C.hex || exit /b 1
avr-size -C --mcu=atmega128 firmware\MicroProject_C.elf
