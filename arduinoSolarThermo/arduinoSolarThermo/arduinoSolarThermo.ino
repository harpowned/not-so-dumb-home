#include <Adafruit_BMP085.h>

#include <Wire.h> 
#include <LiquidCrystal_I2C.h>

#define RELAY_ON 0
#define RELAY_OFF 1

#define VERSION 1.01

#define Relay_1  2  // Arduino Digital I/O pin number
#define Relay_2  3
#define Relay_3  4
#define Relay_4  5
#define Relay_5  6
#define Relay_6  7
#define Relay_7  8
#define Relay_8  9

#define Relay_pump 2
#define Relay_callForHeat 3
#define Relay_solar 4

#define Button_mode 10
#define Button_plus 11
#define Button_minus 12

#define BACKLIGHT_PIN     3
#define BACKLIGHT_CYCLES 1000


#define MAX_INPUT 10


// Main FSM possible states
#define MODE_OFF 0
#define MODE_FIRE 1
#define MODE_THERMOSTAT 2

Adafruit_BMP085 bmp;

uint8_t mode_fsm = MODE_OFF;

String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete
int stringLength = 0;

boolean solarActive = false;
float currentTemp = 0.0;
float setPoint = 20.0;
float hysteresis = 3.0;
boolean callForHeat = false;

boolean backlightOn = true;
int backlightCounter = 0;

//LiquidCrystal_I2C lcd(0x3F);
LiquidCrystal_I2C lcd(0x3F, 2, 1, 0, 4, 5, 6, 7);

int lastModeButtonState = LOW;
int lastPlusButtonState = LOW;
int lastMinusButtonState = LOW;

void executeCommandIfPending(){
  if (stringComplete) {
    processCommand(inputString);
    //    Serial.println(inputString);
    // clear the string:
    inputString = "";
    stringLength = 0;
    stringComplete = false;
  }
}

void changeMode(uint8_t newMode){
  mode_fsm = newMode;
  modeFsmTask();
}

void setSolar(bool value){
  lcd.setCursor (0,0);
  lcd.print("Solar|");
  lcd.setCursor(0,1);
  if (value){
    lcd.print("Actiu|");
  } else{
    lcd.print("Parat|");
  }
  solarActive = value;
  modeFsmTask();
}

void setLcdModeOff(){
  lcd.setCursor(6,0);
  lcd.print("  Apagat  ");

}
void setLcdModeFire(){
  lcd.setCursor(6,0);
  lcd.print("   Foc    ");
}
void setLcdModeThermostat(){
  lcd.setCursor(6,0);
  lcd.print("          ");
  lcd.print("Ob:22.5C *");
  printSetPoint();
}
void printSetPoint(){
  lcd.setCursor(6,0);
  lcd.print("Ob:"+String(setPoint,2)+"C");
}
void modeFsmTask(){
  // Solar relay must be active whenever solar is running
  if (solarActive){
    digitalWrite(Relay_solar, RELAY_ON);
  } else {
    digitalWrite(Relay_solar, RELAY_OFF);
  }
  switch (mode_fsm){
    case MODE_OFF:
    default:
      setLcdModeOff();
      // In off mode, pump must be active only if solar
      if (solarActive){
        digitalWrite(Relay_pump, RELAY_ON);
      } else {
        digitalWrite(Relay_pump, RELAY_OFF);
      }
      
      digitalWrite(Relay_callForHeat, RELAY_OFF);
      break;
    case MODE_FIRE:
      setLcdModeFire();
      // If the fire is burning, pump must be always active
      digitalWrite(Relay_pump, RELAY_ON);
      digitalWrite(Relay_callForHeat, RELAY_OFF);
      break;
    case MODE_THERMOSTAT:
      //TODO: Read temp, implement hysteresis
      setLcdModeThermostat();
      // If the thermostat is on, pump must always be active
      digitalWrite(Relay_pump, RELAY_ON);
      digitalWrite(Relay_callForHeat, RELAY_OFF);
      callForHeat = false;
      break;
  }
}

void cycleMode(){
  switch (mode_fsm){
    case MODE_OFF:
    default:
      mode_fsm = MODE_FIRE;
      break;
    case MODE_FIRE:
      mode_fsm = MODE_THERMOSTAT;
      break;
    case MODE_THERMOSTAT:
      mode_fsm = MODE_OFF;
      break;
  }
  modeFsmTask();
}

void setBacklight(boolean backlight){
  if (backlight){
    lcd.setBacklight(HIGH);
  } else {
    lcd.setBacklight(LOW);
  }
  backlightOn = backlight;
}

void setup() {
  lcd.begin(16,2);
  lcd.setBacklightPin(BACKLIGHT_PIN,POSITIVE);
  lcd.setBacklight(HIGH);
  lcd.home ();
  lcd.print("   Termostat   ");  
  lcd.setCursor ( 0, 1 );
  lcd.print ("Iniciant..V     ");
  lcd.setCursor (11,1);
  lcd.print(VERSION);
  
  //-------( Initialize Pins so relays are inactive at reset)----
  digitalWrite(Relay_1, RELAY_OFF);
  digitalWrite(Relay_2, RELAY_OFF);
  digitalWrite(Relay_3, RELAY_OFF);
  digitalWrite(Relay_4, RELAY_OFF);
  digitalWrite(Relay_5, RELAY_OFF);
  digitalWrite(Relay_6, RELAY_OFF);
  digitalWrite(Relay_7, RELAY_OFF);
  digitalWrite(Relay_8, RELAY_OFF);

  //---( THEN set pins as outputs )----
  pinMode(Relay_1, OUTPUT);
  pinMode(Relay_2, OUTPUT);
  pinMode(Relay_3, OUTPUT);
  pinMode(Relay_4, OUTPUT);
  pinMode(Relay_5, OUTPUT);
  pinMode(Relay_6, OUTPUT);
  pinMode(Relay_7, OUTPUT);
  pinMode(Relay_8, OUTPUT);
  pinMode(Button_mode, INPUT);

  // Set the buttons as inputs, and turn on the internal pull-up
  // Buttons are pressed when they are connected to GND
  digitalWrite(Button_mode, HIGH);
  pinMode(Button_plus, INPUT);
  digitalWrite(Button_plus, HIGH);
  pinMode(Button_minus, INPUT);
  digitalWrite(Button_minus, HIGH);
  delay(4000); //Check that all relays are inactive at Reset

  // initialize serial:
  Serial.begin(9600);
  // reserve bytes for the inputString:
  inputString.reserve(MAX_INPUT);

  lcd.clear();
  changeMode(MODE_OFF);
  setSolar(false);
  bmp.begin();
  Serial.write("BOOT\n");
}

void processCommand(String input) {
  if (input.length() >= 3){
      String cmd;
      cmd = input.substring(0,3);
    if (cmd == "slr"){ // COMMAND: Set solar state
        Serial.write("Setting solar to ");
        if (input.length() == 6){
          String param;
          param = input.substring(4,5);
          if (param == "0"){
            Serial.write("off\n");
            setSolar(false);
          } else if (param == "1"){
            Serial.write("on\n");
            setSolar(true);
          } else {
            Serial.write("Invald parameter, no change.\n");
          }
        } else {
          Serial.write("Wrong parameters for slr\n");
        }
    } else if (cmd == "stp"){ // COMMAND: Set mode STOP
        Serial.write("Stopping\n");
        changeMode(MODE_OFF);
    } else if (cmd == "fir"){ // COMMAND: Set mode FIRE
        Serial.write("Setting fire mode\n");
        changeMode(MODE_FIRE);
    } else if (cmd == "the"){ // COMMAND: Set mode THERMOSTAT
        Serial.write("Setting thermostat mode\n");
        changeMode(MODE_THERMOSTAT);
    }
    else if (cmd == "set"){ // COMMAND: Set setpoint
      if (input.length() == 10){
        Serial.print("DEBUG: Setpoint is "+input.substring(4,9)+"\n");
        double newSetPoint;
        newSetPoint = input.substring(4,9).toFloat();
        if (newSetPoint != 0){
          setPoint = newSetPoint;
          if (mode_fsm == MODE_THERMOSTAT){
            printSetPoint();
          }
        } else {
          Serial.write("Invald parameter, no change. Format is \"set 00.00\"\n");
        }
      } else {
        Serial.write("Invald parameter, no change. Format is \"set 00.00\"\n");
      } 
    } else if (cmd == "stt"){ // COMMAND: Query status
      // Open main json
      Serial.write("{");
      // Print solar mode
      Serial.write("\"solar\":");
      if (solarActive){
        Serial.write("true");
      } else {
        Serial.write("false");
      }
      // Field separator
      Serial.write(",");
      // Print operating mode
      Serial.write("\"mode\":\"");
      switch (mode_fsm){
        case MODE_OFF:
        default:
          Serial.write("off");
          break;
        case MODE_FIRE:
          Serial.write("fire");
          break;
        case MODE_THERMOSTAT:
          Serial.write("thermostat");
          break;
      }
      Serial.write("\"");
      // Field separator
      Serial.write(",");
      // Print temperature
      Serial.write("\"temp\":");
      Serial.print(currentTemp);
      // Field separator
      Serial.write(",");
      // Print isHeating
      Serial.write("\"heating\":");
      if ((mode_fsm == MODE_THERMOSTAT) && (callForHeat)){
        Serial.write("true");
      } else {
        Serial.write("false");
      }
      // Field separator
      Serial.write(",");
      // Print setPoint
      Serial.write("\"setpoint\":");
      Serial.print(setPoint);
      // Close main json
      Serial.write("}\n");
    } else {
        Serial.write("Invalid command\n");
    }

  }
}
void updateTemperature(){
  currentTemp = bmp.readTemperature();
  lcd.setCursor(6,1);
  lcd.print(String("Act:"+String(currentTemp,2)+"C"));
}
void run_thermostat(){
  if (callForHeat == false){
    if (currentTemp < (setPoint - (0.5*hysteresis))){
      Serial.write("Now heating\n");
      callForHeat = true;
      digitalWrite(Relay_callForHeat, RELAY_ON);
      lcd.setCursor(15,0);
      lcd.print("*");
    }
  } else { //callForHeat = true
    if (currentTemp > (setPoint + (0.5*hysteresis))){
      Serial.write("Now notheating\n");
      callForHeat = false;
      digitalWrite(Relay_callForHeat, RELAY_OFF);
      lcd.setCursor(15,0);
      lcd.print(" ");
    }
  }
}

void loop() {
  int reading;
  executeCommandIfPending();
  // Read mode button
  reading = digitalRead(Button_mode);
    if (reading != lastModeButtonState) {
      if (reading == LOW) {
        backlightCounter = 0;
        if (backlightOn == false){
          setBacklight(true);
        } else {
          cycleMode();
        }
      }
    }
  lastModeButtonState = reading;
  // Read plus button
  reading = digitalRead(Button_plus);
    if (reading != lastPlusButtonState) {
      if (reading == LOW) {
        backlightCounter = 0;
        if (backlightOn == false){
          setBacklight(true);
        } else {
          if (mode_fsm == MODE_THERMOSTAT){
            setPoint = setPoint + 0.5;
            printSetPoint();
          }
        }
      }
    }
  lastPlusButtonState = reading;
  // Read minus button
  reading = digitalRead(Button_minus);
    if (reading != lastMinusButtonState) {
      if (reading == LOW) {
        backlightCounter = 0;
        if (backlightOn == false){
          setBacklight(true);
        } else {
          if (mode_fsm == MODE_THERMOSTAT){
            setPoint = setPoint - 0.5;
            printSetPoint();
          }
        }
      }
    }
  lastMinusButtonState = reading;
  updateTemperature();
  if (mode_fsm == MODE_THERMOSTAT){
    run_thermostat();
  }
  if (backlightOn == true){
    backlightCounter++;
    if (backlightCounter >= BACKLIGHT_CYCLES){
      setBacklight(false);
    }
  }
  delay(100);
}

/*
  SerialEvent occurs whenever a new data comes in the
  hardware serial RX.  This routine is run between each
  time loop() runs, so using delay inside loop can delay
  response.  Multiple bytes of data may be available.
*/
void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    if (stringLength >= MAX_INPUT) {
      inputString = "";
      stringLength = 0;
    } else {
      // add it to the inputString:
      inputString += inChar;
      // if the incoming character is a newline, set a flag
      // so the main loop can do something about it:
      if (inChar == '\n') {
        stringComplete = true;
      }
      stringLength++;
    }

  }
}

