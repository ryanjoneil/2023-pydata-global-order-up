# Order up! How do I deliver it?

## Build on-demand logistics apps with Python, OR-Tools, and DecisionOps

Ryan O’Neil  
December 6, 2023  
PyData Global  
[slides](slides.pdf)

You can use this repository to follow along with the talk and make changes to
the models. There are three OR-Tools models.

* `forecast`: demand forecasting using LAD regression
* `schedule`: driver scheduling based on demand and availability
* `route`: driver routing based on demand and capacity

You can run each model the same way. The example below shows how to run the
forecasting model. Substitute `schedule` or `route` for `forecast to run the
other two.

```bash
$ cd forecast
forecast$ python main.py < input.json
{
    ...snip...
}
```

Make sure you have the libraries specified in 
[`requirements.txt`](requirements.txt) installed.

If you have a [Nextmv Cloud](https://cloud.nextmv.io/) account and the `nextmv`
CLI installed, you can deploy any of these models into an app.

```bash
forecast$ nextmv app push -a $APP_ID
forecast$ nextmv app run -a $APP_ID -i input.json -w
{
    ...snip...
}
```
