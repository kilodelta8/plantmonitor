/*
 * waterpumpTest.c
 * 
 * Tests the water pump relay connected to Arduino Pin 7 (PD7).
 * Logic: Toggles PD7 High (Pump ON) and Low (Pump OFF).
 * 
 * Target: ATmega328P (Arduino Uno)
 * Compile: avr-gcc -Os -DF_CPU=16000000UL -mmcu=atmega328p -c -o waterpumpTest.o waterpumpTest.c
 */

#include <avr/io.h>
#include <util/delay.h>

#define RELAY_PIN PD7
#define RELAY_PORT PORTD
#define RELAY_DDR DDRD

// Define relay logic (Low Level Trigger assumed for generic modules)
// LOW = ON, HIGH = OFF
#define RELAY_ON_STATE  0 
#define RELAY_OFF_STATE 1

int main(void) {
    // Setup
    // Configure RELAY_PIN (PD7) as Output
    RELAY_DDR |= (1 << RELAY_PIN);

    // Initialize as OFF (High)
    if (RELAY_OFF_STATE) {
        RELAY_PORT |= (1 << RELAY_PIN);
    } else {
        RELAY_PORT &= ~(1 << RELAY_PIN);
    }

    // Loop
    while (1) {
        // 1. Turn Pump ON
        if (RELAY_ON_STATE) {
             RELAY_PORT |= (1 << RELAY_PIN);
        } else {
             RELAY_PORT &= ~(1 << RELAY_PIN);
        }
        
        // Wait 3 seconds
        _delay_ms(3000);

        // 2. Turn Pump OFF
        if (RELAY_OFF_STATE) {
             RELAY_PORT |= (1 << RELAY_PIN);
        } else {
             RELAY_PORT &= ~(1 << RELAY_PIN);
        }

        // Wait 5 seconds
        _delay_ms(5000);
    }

    return 0;
}
