var Payment = artifacts.require("./Payment.sol");
// var HelloWorld = artifacts.require("./HelloWorld.sol")

module.exports = function(deployer) {
  deployer.deploy(Payment);
  // deployer.deploy(HelloWorld);
};
