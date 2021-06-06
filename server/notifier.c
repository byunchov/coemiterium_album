#include <stdio.h>
#include <stdlib.h>
#include <sqlite3.h>
#include <string.h>
#include <mosquitto.h>
#include <time.h>

#define MAX_TOPIC_SIZE 80
#define MAX_MSG_SIZE 128

// A date has day 'd', month 'm' and year 'y'
typedef struct
{
    int d, m, y;
} Date;

// Date today = {31, 5, 2021};
Date today;

// To store number of days in all months from January to Dec.
const int monthDays[12] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
const char *notif_msg = "Изминаха %s от смъртта на %s.";
const char *pub_topic = "coemiterium/notification/%s";

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

// This function counts number of leap years before the given date
int count_leap_years(Date d)
{
    int years = d.y;

    // Check if the current year needs to be considered leap
    if (d.m <= 2)
        years--;

    return years / 4 - years / 100 + years / 400;
}

// This function returns number of days between two given dates
int get_difference(Date dt1, Date dt2)
{

    long int n1 = dt1.y * 365 + dt1.d;

    for (int i = 0; i < dt1.m - 1; i++)
        n1 += monthDays[i];

    n1 += count_leap_years(dt1);

    long int n2 = dt2.y * 365 + dt2.d;
    for (int i = 0; i < dt2.m - 1; i++)
        n2 += monthDays[i];
    n2 += count_leap_years(dt2);

    // return difference between two counts
    return (n2 - n1);
}

static int callback(void *data, int argc, char **argv, char **azColName)
{
    char date[12] = {0};
    char *delim = "-";
    char topic[MAX_TOPIC_SIZE] = {0};
    char msg[MAX_MSG_SIZE] = {0};
    Date d;

    strncpy(date, argv[0], 12);

    char *ptr = strtok(date, delim);
    d.y = atoi(ptr);
    ptr = strtok(NULL, delim);
    d.m = atoi(ptr);
    ptr = strtok(NULL, delim);
    d.d = atoi(ptr);

    // printf("Parsed date is: %d.%d.%d\n", d.d, d.m, d.y);
    snprintf(topic, MAX_TOPIC_SIZE, pub_topic, argv[1]);

    int date_diff = get_difference(d, today);
    if (date_diff == 40 || date_diff == 41)
    {
        snprintf(msg, MAX_MSG_SIZE, notif_msg, "40 дни", argv[2]);
        notify_mqtt(topic, msg);
    }
    else if (date_diff == 182 || date_diff == 183)
    {
        snprintf(msg, MAX_MSG_SIZE, notif_msg, "6 месеца", argv[2]);
        notify_mqtt(topic, msg);
    }
    else if (date_diff == 365 || date_diff == 366)
    {
        snprintf(msg, MAX_MSG_SIZE, notif_msg, "1 годинa", argv[2]);
        notify_mqtt(topic, msg);
    }
    else if (date_diff == 730 || date_diff == 731)
    {
        snprintf(msg, MAX_MSG_SIZE, notif_msg, "2 години", argv[2]);
        notify_mqtt(topic, msg);
        // printf("2y UID: %s\n", argv[1]);
        // printf("Изминаха 2 години от смъртта на %s.\n", argv[2]);
    }
    else if (date_diff == 1095 || date_diff == 1096)
    {
        snprintf(msg, MAX_MSG_SIZE, notif_msg, "3 години", argv[2]);
        notify_mqtt(topic, msg);
    }
    else if (date_diff == 1825 || date_diff == 1826)
    {
        snprintf(msg, MAX_MSG_SIZE, notif_msg, "5 години", argv[2]);
        notify_mqtt(topic, msg);
    }
    else if (date_diff == 3650 || date_diff == 3651)
    {
        snprintf(msg, MAX_MSG_SIZE, notif_msg, "10 години", argv[2]);
        notify_mqtt(topic, msg);
    }
    else if (date_diff == 7300 || date_diff == 7301)
    {
        snprintf(msg, MAX_MSG_SIZE, notif_msg, "20 години", argv[2]);
        notify_mqtt(topic, msg);
    }

    return 0;
}

void set_current_date()
{
    time_t t = time(NULL);
    struct tm tm = *localtime(&t);
    today.d = tm.tm_mday;
    today.m = tm.tm_mon + 1;
    today.y = tm.tm_year + 1900;

    // printf("now: %d-%02d-%02d %02d:%02d:%02d\n", tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
}

// Driver code
int main()
{
    // Date dt1 = {31, 5, 2019};
    // Date dt2 = {1, 2, 2004};

    // // Function call
    // printf("Difference between two dates is %d\n", get_difference(dt1, today));

    set_current_date();

    sqlite3 *db;
    char *zErrMsg = {0};
    int rc;

    char *sql = "SELECT dod, token, (first_name || ' ' ||  last_name) as name from deceased_list;";

    /* Open database */
    rc = sqlite3_open("coemiterium.db", &db);

    if (rc)
    {
        fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
        exit(2);
    }

    rc = sqlite3_exec(db, sql, callback, NULL, &zErrMsg);

    if (rc != SQLITE_OK)
    {
        fprintf(stderr, "SQL error: %s\n", zErrMsg);
        sqlite3_free(zErrMsg);
    }
    sqlite3_close(db);

    return 0;
}