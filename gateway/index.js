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

app.get('/', function(req,res){
  res.sendFile(path.join(__dirname,'./public/index.html'));
});

app.post('/', async (req, res) => {
  const name = process.env.NAME || 'World';
  
  if (!req.body.car_id)
      return console.error('missing car id');

  if (!req.body.to_email)
    return console.error('missing dest email');

  // Execute workflow
  try {
      const createExecutionRes = await client.createExecution({
          execution: {
              argument: JSON.stringify({
                car_id: req.body.car_id,
                to_email: req.body.to_email,
                search_id: searchId,
                search_cx: searchCx,
              }),
          },
          parent: client.workflowPath(projectId, 'europe-west4', workflow),
      });
      console.log(`Here: ${createExecutionRes}`);

      const executionName = createExecutionRes[0].name;
      console.log(`Created execution: ${executionName}`);
      res.send(`Request dispatched! Request ID: ${executionName}, Please check your mail!`)
  
  } catch (e) {
      console.error(`Error executing workflow: ${e} ${e.stack}`);
      res.send(`Error in dispatching request!`)
  }
});

if (!projectId)
  return console.error('ERROR: GOOGLE_CLOUD_PROJECT is required.');

if (!searchId)
  return console.error('ERROR: SEARCH_ID is required.');

if (!searchCx)
  return console.error('ERROR: SEARCH_CX is required.');


const port = process.env.PORT || 8080;
app.listen(port, () => {
  console.log(`helloworld: listening on port ${port}`);
});