/*
 * capacitiveTest.c
 *
 * Tests the capacitive soil moisture sensor on Analog Pin A0 (ADC0/PC0).
 * Logic: Reads ADC value and prints to Serial (UART) at 9600 baud.
 *
 * Target: ATmega328P (Arduino Uno)
 * Compile: avr-gcc -Os -DF_CPU=16000000UL -mmcu=atmega328p -c -o
 * capacitiveTest.o capacitiveTest.c
 */

#include <avr/io.h>
#include <stdio.h>
#include <util/delay.h>

#define F_CPU 16000000UL
#define BAUD 9600
#define UBRR_VALUE ((F_CPU / (16UL * BAUD)) - 1)

// Initialize UART for Serial Communication
void uart_init(void) {
  // Set baud rate
  UBRR0H = (unsigned char)(UBRR_VALUE >> 8);
  UBRR0L = (unsigned char)UBRR_VALUE;

  // Enable transmitter
  UCSR0B = (1 << TXEN0);

  // Set frame format: 8data, 1stop bit
  UCSR0C = (1 << UCSZ01) | (1 << UCSZ00);
}

// Send a single character
void uart_transmit(unsigned char data) {
  // Wait for empty transmit buffer
  while (!(UCSR0A & (1 << UDRE0)))
    ;

  // Put data into buffer, sends the data
  UDR0 = data;
}

// Send a string
void uart_print(const char *str) {
  while (*str) {
    uart_transmit(*str++);
  }
}

// Helper to convert integer to string and print
void uart_print_int(int val) {
  char buffer[10];
  sprintf(buffer, "%d", val);
  uart_print(buffer);
}

// Initialize ADC
void adc_init(void) {
  // Reference: AVcc with external capacitor on AREF pin
  // MUX: 0000 for ADC0 (PC0 / A0)
  ADMUX = (1 << REFS0);

  // Enable ADC, Set Prescaler to 128 (16MHz/128 = 125kHz)
  // ADC needs 50-200kHz
  ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);
}

// Read ADC value from Channel 0
uint16_t adc_read(void) {
  // Start conversion
  ADCSRA |= (1 << ADSC);

  // Wait for conversion to complete
  while (ADCSRA & (1 << ADSC))
    ;

  // Return result
  return ADC;
}

int main(void) {
  // Setup
  uart_init();
  adc_init();

  uart_print("Capacitive Soil Moisture Sensor Test (AVR C)\r\n");
  uart_print("--------------------------------------------\r\n");

  // Loop
  while (1) {
    uint16_t sensorValue = adc_read();

    uart_print("Raw Sensor Value: ");
    uart_print_int(sensorValue);
    uart_print("\r\n");

    _delay_ms(2000);
  }

  return 0;
}
