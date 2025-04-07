const chatListTest = require('./chat-list.test');
const imagePickerTest = require('./image-picker.test');
const locationPickerTest = require('./location-picker.test');
const memoryUsageTest = require('./memory-usage.test');

/**
 * 运行所有测试
 */
const runAllTests = function() {
  console.log('======================================');
  console.log('开始运行微信小程序测试套件');
  console.log('======================================');
  
  const chatListResult = chatListTest.runAllTests();
  console.log('\n');
  
  const imagePickerResult = imagePickerTest.runAllTests();
  console.log('\n');
  
  const locationPickerResult = locationPickerTest.runAllTests();
  console.log('\n');
  
  const memoryUsageResult = memoryUsageTest.runAllTests();
  console.log('\n');
  
  const allPassed = chatListResult && imagePickerResult && locationPickerResult && memoryUsageResult;
  
  console.log('======================================');
  console.log('测试结果汇总');
  console.log('======================================');
  console.log(`聊天列表测试：${chatListResult ? '通过' : '失败'}`);
  console.log(`图片选择测试：${imagePickerResult ? '通过' : '失败'}`);
  console.log(`位置选择测试：${locationPickerResult ? '通过' : '失败'}`);
  console.log(`内存使用测试：${memoryUsageResult ? '通过' : '失败'}`);
  console.log('--------------------------------------');
  console.log(`总体结果：${allPassed ? '通过' : '失败'}`);
  console.log('======================================');
  
  return allPassed;
};

if (require.main === module) {
  runAllTests();
}

module.exports = {
  runAllTests
};
