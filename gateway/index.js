const express = require('express');
const app = express();
const path = require("path");
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(path.join(__dirname,'./public')));

const {ExecutionsClient} = require('@google-cloud/workflows');
const client = new ExecutionsClient();

const projectId = process.env.GOOGLE_CLOUD_PROJECT;
const searchId = process.env.SEARCH_ID;
const searchCx = process.env.SEARCH_CX;
const workflow = 'mail';

function sleep(ms) {
    return new Promise(resolve => {
      setTimeout(resolve, ms);
    });
  }

app.get('/', function(req,res){
  res.sendFile(path.join(__dirname,'./public/index.html'));
});

app.post('/', async (req, res) => {
  const name = process.env.NAME || 'World';

  if (!projectId)
    return console.error('ERROR: GOOGLE_CLOUD_PROJECT is required.');

  if (!searchId)
  return console.error('ERROR: SEARCH_ID is required.');

  if (!searchCx)
  return console.error('ERROR: SEARCH_CX is required.');

  if (!req.body.car_id)
      return console.error('missing car id');

  // Execute workflow
    try {
        const createExecutionRes = await client.createExecution({
            execution: {
                argument: JSON.stringify({
                  car_id: req.body.car_id,
                  search_id: searchId,
                  search_cx: searchCx,
                }),
            },
            parent: client.workflowPath(projectId, 'europe-west4', workflow),
        });
        console.log(`Here: ${createExecutionRes}`);

        const executionName = createExecutionRes[0].name;
        console.log(`Created execution: ${executionName}`);
    
        // Wait for execution to finish, then print results.
        let executionFinished = false;
        let backoffDelay = 1000; // Start wait with delay of 1,000 ms
        console.log('Poll every second for result...');
        while (!executionFinished) {
        const [execution] = await client.getExecution({
            name: executionName,
        });
        executionFinished = execution.state !== 'ACTIVE';
    
        // If we haven't seen the result yet, wait a second.
        if (!executionFinished) {
            console.log('- Waiting for results...');
            await sleep(backoffDelay);
            backoffDelay *= 2; // Double the delay to provide exponential backoff.
        } else {
            console.log(`Execution finished with state: ${execution.state}`);
            console.log(execution.result);
            res.send(execution.result);
            return;
        }
        }
    } catch (e) {
        console.error(`Error executing workflow: ${e} ${e.stack}`);
    }

  res.send(`Hello ${name}!`);

});

const port = process.env.PORT || 8080;
app.listen(port, () => {
  console.log(`helloworld: listening on port ${port}`);
});