#include <stdio.h>
#include <stdlib.h>
#include <sqlite3.h>
#include <string.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdbool.h>

#define BUF_SIZE 1024
#define SERVER_PORT 50555
#define SERVER_BACKLOG 10
#define SOCK_ERR (-1)

typedef struct sockaddr_in SA_IN;
typedef struct sockaddr SOCK_ADR;
const char *exit_msg = "#!:exit:";

void handle_connection(int client_socket);
int error_check(int exp, const char *msg);

static int callback(void *data, int argc, char **argv, char **azColName)
{
   int i;
   char res[BUF_SIZE] = {0};

   // fprintf(stderr, "%s: ", (const char *)data);

   for (i = 0; i < argc; i++)
   {
      if (i > 0)
         strncat(res, "|", 2);

      strncat(res, argv[i], strlen(argv[i]));
      // printf("%s = %s\n", azColName[i], argv[i] ? argv[i] : "NULL");
   }
   // write(*((int*)data), res, strlen(res));

   printf("%s\n", res);
   usleep(10);
   if (strlen(res) > 0)
      send(*((int *)data), res, strlen(res), 0);

   return 0;
}

int main(int argc, char *argv[])
{

   int server_socket, client_socket, addr_size;
   SA_IN server_addr, client_addr;

   error_check((server_socket = socket(AF_INET, SOCK_STREAM, 0)), "Failed to create socket!");

   server_addr.sin_family = AF_INET;
   server_addr.sin_addr.s_addr = INADDR_ANY;
   server_addr.sin_port = htons(SERVER_PORT);

   error_check(bind(server_socket, (SOCK_ADR *)&server_addr, sizeof(server_addr)), "Binding failed!");

   error_check(listen(server_socket, SERVER_BACKLOG), "Listen failed!");

   while (true)
   {
      printf("Waiting for connections...\n");
      addr_size = sizeof(SA_IN);

      error_check((client_socket = accept(server_socket, (SOCK_ADR *)&client_addr, (socklen_t *)&addr_size)), "Accept failed!");

      printf("Connected\n");
      handle_connection(client_socket);
   }

   return 0;
}

void handle_connection(int client_socket)
{
   char buffer[BUF_SIZE] = {0};
   char error_msg[128] = {0};
   char last_insert_id[12] = {0};
   size_t bytes_read;
   int msg_size = 0;

   sqlite3 *db;
   char *zErrMsg = {0};
   int rc;

   /* Open database */
   rc = sqlite3_open("coemiterium.db", &db);

   if (rc)
   {
      fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
      exit(2);
   }
   else
   {
      fprintf(stderr, "Opened database successfully\n");
   }

   // while ((bytes_read = read(client_socket, buffer + msg_size, sizeof(buffer) - msg_size - 1)) > 0)
   // {
   //    msg_size += bytes_read;

   //    if (msg_size > (BUF_SIZE - 1) || buffer[msg_size - 1] == '\n')
   //       break;
   // }
   bytes_read = recv(client_socket, buffer, BUF_SIZE, 0);

   printf("Request: %s\n", buffer);
   fflush(stdout);

   /* Create SQL statement */
   // sql = "SELECT grave_sites.zone,  grave_sites.sector,grave_sites.row, grave_sites.num, owners_list.first_name, owners_list.last_name from grave_sites JOIN owners_list on grave_sites.owner=owners_list.id;";

   // sql = "select * from owners_list order by first_name limit 5;";
   /* Execute SQL statement */
   rc = sqlite3_exec(db, buffer, callback, (int *)&client_socket, &zErrMsg);

   if (rc != SQLITE_OK)
   {
      fprintf(stderr, "SQL error: %s\n", zErrMsg);
      snprintf(error_msg, 128, "!#error: %s", zErrMsg);
      send(client_socket, error_msg, strlen(error_msg), 0);
      sqlite3_free(zErrMsg);
   }
   else
   {
      fprintf(stdout, "Operation done successfully\n");
   }

   long last_id = sqlite3_last_insert_rowid(db);
   if (last_id > 0)
   {
      snprintf(last_insert_id, 12, "%ld", last_id);
      send(client_socket, last_insert_id, strlen(last_insert_id), 0);
      printf("The last Id of the inserted row is %ld\n", last_id);
   }

   sqlite3_close(db);
   send(client_socket, exit_msg, strlen(exit_msg), 0);
   close(client_socket);
   printf("Closing connection\n");

   // error_check(bytes_read, "recv() error");
   // buffer[msg_size - 1] = '\0';
}

int error_check(int exp, const char *msg)
{
   if (exp == SOCK_ERR)
   {
      perror(msg);
      exit(1);
   }
   return exp;
}