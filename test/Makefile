# Makefile for Plant Monitor AVR Tests
#
# Usage:
#   make all        - Compile both tests
#   make waterpump  - Compile waterpumpTest.c
#   make capacitive - Compile capacitiveTest.c
#   make clean      - Remove build artifacts

MCU=atmega328p
F_CPU=16000000UL
CC=avr-gcc
CFLAGS=-Os -DF_CPU=$(F_CPU) -mmcu=$(MCU)

all: waterpump capacitive

waterpump: waterpumpTest.c
	$(CC) $(CFLAGS) -c -o waterpumpTest.o waterpumpTest.c
	$(CC) $(CFLAGS) -o waterpumpTest.elf waterpumpTest.o
	avr-objcopy -O ihex -R .eeprom waterpumpTest.elf waterpumpTest.hex

capacitive: capacitiveTest.c
	$(CC) $(CFLAGS) -c -o capacitiveTest.o capacitiveTest.c
	$(CC) $(CFLAGS) -o capacitiveTest.elf capacitiveTest.o
	avr-objcopy -O ihex -R .eeprom capacitiveTest.elf capacitiveTest.hex

clean:
	rm -f *.o *.elf *.hex
