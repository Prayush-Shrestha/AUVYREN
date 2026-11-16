import 'package:flutter_test/flutter_test.dart';

import 'package:auvyren_mobile/main.dart';

void main() {
  testWidgets('AuvyrenApp builds without crashing', (WidgetTester tester) async {
    await tester.pumpWidget(const AuvyrenApp());
    expect(find.byType(AuvyrenApp), findsOneWidget);
  });
}
