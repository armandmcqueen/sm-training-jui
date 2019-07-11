# SageMaker training job

`Dockerfile` and `resources/` hold the SageMaker compatible container.

`run_estimator.py` holds the code to launch the training using the SageMaker SDK.

`tasks.py` holds logic to build and push the container. It uses the [invoke](http://www.pyinvoke.org/) library so usage is:

```
$ invoke drun
$ invoke dbuild
$ invoke decr
```
