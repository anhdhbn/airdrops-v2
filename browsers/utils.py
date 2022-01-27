from subprocess import Popen, PIPE
import shlex

def run_command(command, callback=None):
	with Popen(shlex.split(command), stdout=PIPE, stderr=PIPE, universal_newlines=True) as process:
		while True:
			output = process.stdout.readline()
			if output == '' and process.poll() is not None:
				break
			if output:
				print(output.strip())
		rc = process.poll()
		if rc is None:
			process.kill()
		if callback:
			error_output = process.stderr.readlines()
			callback(error_output)
		
		process.stdout.close()
		process.stderr.close()
		process.terminate()
	return rc
