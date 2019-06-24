# Using Container As Basis For Horovod Training on SageMaker

* At the very beginning of your `train` script, you must call `sagemaker_hvd_setup.run()`. 
    * This will launch ssh daemons on each node and wait until they are available
    * This will dynamically apply a patch to fix gethostname() behaviour that OpenMPI relies on 
    * This will save the environment variable for ECS container credentials to .bashrc so processes launched by mpirun on a worker node can see it
* The mpirun command must include `-x LD_PRELOAD=/libchangehostname.so`
* The mpirun command must be run on only one node. The other nodes must not exit until the training is complete
    * The 'master' node should be the node with the first hostname in an alphabetically sorted list. This is arbitrary, but important because `sagemaker_hvd_setup.run()` uses this logic.  
    * Be careful here as it is easy to come up with a solution that does not shut down the worker nodes when there is a failure in the master node.
    * `sagemaker_hvd_utils.py` has one possible way to accomplish this - it is only acceptable for closely monitored jobs as it appears it can keep the job running after master node has failed.
    * Afetr training is complete, MPI must do some cleanup. If the SM container immediately exists after successful training, this can lead to errors on the master container. To avoid this we wait for 1 minute after training completes on the worker containers. Solution is untested
