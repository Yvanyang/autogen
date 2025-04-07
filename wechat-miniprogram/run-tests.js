const tests = require('./tests/index');

console.log('======================================');
console.log('微信小程序测试运行器');
console.log('======================================');
console.log('开始运行所有测试...\n');

const result = tests.runAllTests();

console.log('\n======================================');
console.log(`测试总结: ${result ? '所有测试通过' : '部分测试失败'}`);
console.log('======================================');

process.exit(result ? 0 : 1);
