#include <Servo.h>
Servo servo;int angle=90;void setup(){Serial.begin(9600);servo.attach(9);servo.write(angle);}void loop(){if(!Serial.available())return;String c=Serial.readStringUntil('\n');c.trim();if(c=="+")angle++;else if(c=="-")angle--;else if(c==">")angle+=5;else if(c=="<")angle-=5;else angle=c.toInt();angle=constrain(angle,0,180);servo.write(angle);Serial.println(angle);}
