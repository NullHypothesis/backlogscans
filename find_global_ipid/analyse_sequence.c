/* This tool tells you whether a given sequence of consecutive IPID values is
 * likely to come from a global IPID machine (return code 0) or not (return
 * code 1).
 *
 * You can compile the tool as follows:
 * $ gcc -o analyse_sequence analyse_sequence.c
 *
 * The input is read from stdin.  Every line must be an integer in the
 * range 0 <= n <= 65535.  Examples:
 *
 * $ echo "10\n11\n12\n13" | ./analyse_sequence
 * Given IPID sequence likely to be global.
 * $ echo $?
 * 0
 *
 * $ echo "10\n11\n12\n50" | ./analyse_sequence
 * Given IPID sequence probably *not* global.
 * $ echo $?
 * 1
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#define BUF_SIZE    4096

/* Threshold between two consecutive IPIDs above which a machine is no longer
 * considered to have a global IPID.
 */
#define IPID_DIFF_THRESHOLD    ((uint16_t) 10)

inline int is_sequential( uint16_t ipid0, uint16_t ipid1 ) {

	if (((uint16_t) (ipid1 - ipid0)) > IPID_DIFF_THRESHOLD) {
		return 0;
	} else if (((uint16_t) (ipid1 - ipid0)) == 0) {
		return 0;
	} else {
		return 1;
	}
}

int main( void ) {

    uint16_t crnt_val = 0;
    uint16_t prev_val = 0;
    ssize_t len = 0;
    char *buf = NULL;
    size_t n = BUF_SIZE;
    int ready = 0;

    buf = (char *) malloc((size_t) BUF_SIZE);
    if (buf == NULL) {
        fprintf(stderr, "Error: malloc() failed.\n");
        return 2;
    }

    while ((len = getline(&buf, &n, stdin)) != -1) {

        crnt_val  = (uint16_t) atoi(buf);

        if (ready && !is_sequential(prev_val, crnt_val)) {
            printf("Given IPID sequence probably *not* global.\n");
            return 1;
        }

        prev_val = crnt_val;
        ready = 1;
    }

    printf("Given IPID sequence likely to be global.\n");

    return 0;
}
