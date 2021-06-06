#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mosquitto.h>

int notify_mqtt(char *topic, char *msg)
{
    int rc;
    struct mosquitto *mosq;

    mosquitto_lib_init();

    mosq = mosquitto_new("coemiteruim_pub_client", true, NULL);

    rc = mosquitto_connect(mosq, "localhost", 1883, 60);
    if (rc != 0)
    {
        printf("Client could not connect to broker! Error Code: %d\n", rc);
        mosquitto_destroy(mosq);
        return -1;
    }
    printf("Connected to the broker!\n");

    mosquitto_publish(mosq, NULL, topic, strlen(msg), msg, 0, false);

    mosquitto_disconnect(mosq);
    mosquitto_destroy(mosq);

    mosquitto_lib_cleanup();
    return 0;
}

int main()
{
    int rc = notify_mqtt("coemiterium/notification/dbd25685-da33-4b28-9462-8be95c3655d1", "hello there");

    if (rc == -1)
        exit(1);    
    
    return 0;
}