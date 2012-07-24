#ifndef Sensor_h
#define Sensor_h

#include <Arduino.h>
#include "../config.h"

// The interface that sensors implement.
class Sensor
{
  public:
    // sensor_prefix is a string that will be printed in messages from the sensor.
    explicit Sensor(const char *sensor_prefix);
    virtual ~Sensor();

    // Read data from the sensor and store it.
    virtual void read() = 0;
    // Return whatever buffered data has been read.
    virtual char *get_data() = 0;

  protected:
    const char *prefix_;
};

class Potentiometer : public Sensor
{
  public:
    Potentiometer(const char *sensor_prefix, const byte potPin);
    virtual ~Potentiometer();

    // Sensor interface:
    virtual void read();
    virtual char *get_data();

  private:
    const byte pin_;
    unsigned int last_value_;
};

class Sonar : public Sensor
{
  public:
    Sonar(const char *sensor_prefix, const byte sonarPin);
    virtual ~Sonar();

    // Sensor interface
    virtual void read();
    virtual char *get_data();

  private:
    const byte pin_;
    unsigned int last_value_;
};

#if defined(USE_AMG)
#include "L3G4200D/L3G4200D.h"
#include "LSM303/LSM303.h"

class AMG : public Sensor
{
  public:
    AMG(const char *sensor_prefix);

    void init();
    virtual ~AMG();

    // Sensor interface
    virtual void read();
    virtual char *get_data();

  private:
    bool initialized_;

    L3G4200D gyro_;
    LSM303 compass_;

    struct vector {
      vector() : x(0), y(0), z(0) {}
      float x, y, z;
    };

    vector a_;   //accelerometer
    vector m_;   //magnetometer
    vector g_;   //gyroscope
};
#endif

#endif
