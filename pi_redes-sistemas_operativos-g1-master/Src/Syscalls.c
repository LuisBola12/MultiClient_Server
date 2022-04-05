#include "sys/mman.h"
#include "unistd.h"
#include <stdio.h>
#include <stdlib.h>
#include "stdbool.h"

/**
 * @brief Estructure for the pipe
 * 
 */
typedef struct {
    char *  message;
    int size;
}pipe_t;

/**
 * @brief Create a shared memory with the struct pipe_t
 * 
 * @param size size of the pipe
 * @return pipe_t* 
 */
pipe_t * sys_pipe(int size) {
    int protection = PROT_READ | PROT_WRITE;
    int visibility = MAP_SHARED | MAP_ANONYMOUS;
    pipe_t * pipe = (pipe_t*)mmap(0, 1, protection, visibility , -1, 0);
    pipe->message = (char*)calloc(size,sizeof(char));
    return pipe;
};
 /**
  * @brief Write in the pipe (struct pipe_T)
  * 
  * @param my_pipe struc pipe_t
  * @param buffer message
  */
void sys_write(pipe_t * my_pipe, char * buffer) {
    my_pipe->message = buffer;
};

/**
 * @brief Read the message in the pipe
 * 
 * @param my_pipe struct pipe_t
 * @return char* 
 */
char * sys_read(pipe_t * my_pipe) {
    char * mensaje = my_pipe->message;
    my_pipe->message = (char*)"";
    return mensaje;
};


int main(){
    pipe_t * pipe = sys_pipe(4096);
    int pid = fork();
    if(pid != 0){
        char * message = (char*)"Message sent from other process\n";
        sys_write(pipe,message);
        printf("Message sent from %i \n", getpid());
    }else{
        while(true){
            char * message = sys_read(pipe);
            if(message != ""){
                printf("Message read by: %i message: %s",getpid(),message);
                break;
            }
        }
    }
}
