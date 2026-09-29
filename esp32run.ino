#include <ESP32Servo.h>

Servo servo;

String command = "";
bool scanEnabled = true;

const int SERVO_PIN = 18;
const int TRIG_PIN = 5;
const int ECHO_PIN = 19;
const int LED_PIN = 2;
const int DETECTION_DISTANCE = 50;

long getDistanceCM()
{
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);

  if (duration == 0)
    return -1;

  return duration * 0.0343 / 2;
}

void setup()
{
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  servo.attach(SERVO_PIN);
  servo.write(0);

  Serial.println("SYSTEM STARTED");
}

void loop()
{
  if (Serial.available())
  {
    command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "STOP")
    {
      scanEnabled = false;
      digitalWrite(LED_PIN, HIGH);
      Serial.println("SCAN STOPPED");
    }

    if (command == "RESUME")
    {
      scanEnabled = true;
      digitalWrite(LED_PIN, LOW);
      Serial.println("SCAN RESUMED");
    }
  }

  if (!scanEnabled)
  {
    delay(50);
    return;
  }

  for (int angle = 0; angle <= 180; angle++)
  {
    servo.write(angle);

    if (!scanEnabled)
      return;

    long distance = getDistanceCM();

    Serial.print("Angle: ");
    Serial.print(angle);
    Serial.print(" | Distance: ");

    if (distance == -1)
      Serial.println("No reading");
    else
    {
      Serial.print(distance);
      Serial.println(" cm");
    }

    if (distance > 0 && distance <= DETECTION_DISTANCE)
    {
      servo.write(angle);
      digitalWrite(LED_PIN, HIGH);
      Serial.println("OBJECT DETECTED - SERVO STOPPED");

      while (true)
      {
        long newDistance = getDistanceCM();

        if (newDistance <= 0 || newDistance > DETECTION_DISTANCE)
        {
          digitalWrite(LED_PIN, LOW);
          Serial.println("OBJECT CLEARED - RESUMING SCAN");
          break;
        }

        delay(100);
      }
    }

    delay(30);
  }

  for (int angle = 180; angle >= 0; angle--)
  {
    servo.write(angle);

    long distance = getDistanceCM();

    Serial.print("Angle: ");
    Serial.print(angle);
    Serial.print(" | Distance: ");

    if (distance == -1)
      Serial.println("No reading");
    else
    {
      Serial.print(distance);
      Serial.println(" cm");
    }

    if (distance > 0 && distance <= DETECTION_DISTANCE)
    {
      servo.write(angle);
      digitalWrite(LED_PIN, HIGH);
      Serial.println("OBJECT DETECTED - SERVO STOPPED");

      while (true)
      {
        long newDistance = getDistanceCM();

        if (newDistance <= 0 || newDistance > DETECTION_DISTANCE)
        {
          digitalWrite(LED_PIN, LOW);
          Serial.println("OBJECT CLEARED - RESUMING SCAN");
          break;
        }

        delay(100);
      }
    }

    delay(30);
  }
}
